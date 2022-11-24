#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from typing import Union, Type, Optional, Sequence

from hwt.hdl.operator import Operator
from hwt.hdl.operatorDefs import EVENT_OPS
from hwt.hdl.portItem import HdlPortItem
from hwt.hdl.statements.statement import HdlStatement
from hwt.hdl.value import HValue
from hwt.interfaces.std import Clk, Rst, Rst_n, Signal
from hwt.pyUtils.uniqList import UniqList
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal, OperatorCaheKeyType
from hwt.synthesizer.rtlLevel.rtlSyncSignal import RtlSyncSignal
from hwt.synthesizer.rtlLevel.signalUtils.exceptions import SignalDriverErr
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.componentBuilder import AbstractComponentBuilder


def consumeExpr(e: Union[RtlSignal, HValue],
                inputs:UniqList[RtlSignal],
                seenObjs: UniqList[Union[RtlSignal, Operator]]):
    """
    To make output code readable we must extract also expressions used in statements if they are private
    to selected statements.
    
    :note: Walk from endpoint to a driver. For every signal on path if all its endpoints are
        in seenObjs, add this to seenObjs and continue search on its drivers. 
    """
    if isinstance(e, HValue):
        return

    try:
        d = e.singleDriver()
    except SignalDriverErr:
        seenObjs.append(e)
        inputs.append(e)
        return
        
    if isinstance(d, (HdlPortItem, HdlStatement)):
        seenObjs.append(e)
        inputs.append(e)
        return
    else:
        assert isinstance(d, Operator), d
        d: Operator
        if d.operator in EVENT_OPS:
            c = d.operands[0]
            seenObjs.extend((d, e, c))
            inputs.append(c)
        else:
            for ep in e.endpoints:
                if ep not in seenObjs:
                    inputs.append(e)
                    return

            inputs.discard(e)
            seenObjs.append(e)
            seenObjs.append(d)
            for d in d.operands:
                consumeExpr(d, inputs, seenObjs)


class ExtractedUnit(Unit):
    """
    An unit which will extract selected circuit from parent on instantiation.
    """

    def __init__(self, externInputs: UniqList[RtlSignal],
                  externObjsToExtract: UniqList[Union[RtlSignal, Operator]],
                  externOutputs: UniqList[RtlSignal],
                  hdl_name_override:Optional[str]=None):
        Unit.__init__(self, hdl_name_override=hdl_name_override)
        self._externInputs = externInputs
        self._externObjsToExtract = externObjsToExtract
        self._externOutputs = externOutputs

    def _declr(self) -> None:
        ioMap = self._ioMap = {}
        for i in self._externInputs:
            i: RtlSignal
            intf = getattr(i, "_interface", None)
            iCloned = None
            if intf is not None:
                if isinstance(intf, (Clk, Rst, Rst_n)):
                    iCloned = intf.__class__()
                    iCloned._updateParamsFrom(intf)

            if iCloned is None:
                iCloned = Signal(i._dtype)
            name = AbstractComponentBuilder(self, None, "")._findSuitableName(i.name, firstWithoutCntr=True)
            setattr(self, name, iCloned)
            assert i not in ioMap
            ioMap[i] = iCloned
        
        for o in self._externOutputs:
            o: RtlSignal
            oCloned = Signal(o._dtype)._m()
            name = AbstractComponentBuilder(self, None, "")._findSuitableName(o.name, firstWithoutCntr=True)
            setattr(self, name, oCloned)
            assert o not in ioMap
            ioMap[o] = oCloned

    def _moveOrCopyCircuitFromParent(self):
        # BFS move or copy circuit to this unit from parent
        priv = self._externObjsToExtract
        translation = {i: self._ioMap[i]._sig for i in self._externInputs}
        toTranslate = deque()
        for i in self._externInputs:
            i: RtlSignal
            toTranslate.extend(ep for ep in i.endpoints if ep in priv)

        # if the signal is private, it is necessary to mark it as not hidden
        # in order to provide handle for subexpression replace (_replace_input)
        while toTranslate:
            obj = toTranslate.popleft()
            if obj in translation:
                # already translated
                continue

            if isinstance(obj, HdlStatement):
                stm: HdlStatement = obj
                newInputs = []
                for i in stm._inputs:
                    _i = translation.get(i, None)
                    if _i is None:
                        # postpone until all inputs are translated 
                        newInputs = None
                        break
                    else:
                        assert _i.ctx is self._ctx, (i, _i)
                        newInputs.append(_i)

                if newInputs is None:
                    assert toTranslate, stm
                    toTranslate.append(stm)
                    continue
                
                ctx = stm._get_rtl_context()
                for newI, i in zip(newInputs, stm._inputs):
                    if newI is not i:
                        stm._replace_input((i, newI))
                        
                for o in stm._outputs:
                    o.ctx.signals.remove(o)
                    o.ctx = self._ctx
                    o.ctx.signals.add(o)
                    translation[o] = o
                    toTranslate.extend(ep for ep in o.endpoints if ep in priv)
        
                ctx.statements.remove(stm)
                self._ctx.statements.add(stm)
                translation[stm] = stm
                stm._clean_signal_meta()

            elif isinstance(obj, Operator):
                # shouldCopy = obj.operator in EVENT_OPS
                newOps = []
                for op in obj.operands:
                    if isinstance(op, RtlSignal):
                        _op = translation.get(op)
                        if _op is None:
                            # some input not available yet, must postpone translation
                            newOps = None
                            break
                        else:
                            assert _op.ctx is self._ctx
                            newOps.append(_op)
                    else:
                        assert isinstance(op, HValue), op
                        newOps.append(op)

                if newOps is None:
                    toTranslate.append(obj)
                    continue    

                # if shouldCopy:
                # create a new copy of this object in this unit
                newSig = obj.operator._evalFn(*newOps)
                # parentCtx = obj.result.ctx
                # parentCtx.signals.remove(obj.result)
                # self._ctx.signals.add(obj.result)
                # obj.result.ctx = self._ctx
                
                translation[obj.result] = newSig
                translation[obj] = newSig.singleDriver()
                toTranslate.extend(ep for ep in obj.result.endpoints if ep in priv)
        
                # else:
                #    # move this object to his unit, move is done by translation of operand
                #    # and by move is result signal to the netlist of this unit
                #    raise NotImplementedError(obj)
                
            else:
                raise NotImplementedError(obj.__class__, obj)

        return translation

    def _impl(self) -> None:
        # transfer circuit to subunit
        # re-connect signals which should be connected to IO of new subunit
        translation = self._moveOrCopyCircuitFromParent()
        for o in self._externOutputs:
            self._ioMap[o](translation[o])
    
    def _signalsForSubUnitEntity(self, context: RtlNetlist, prefix: str):
        super(ExtractedUnit, self)._signalsForSubUnitEntity(context, prefix)
        # connect external input signal to a input of this unit
        for i in self._externInputs:
            self._ioMap[i](i)
        
        priv = self._externObjsToExtract
        # for each output to output of this unit
        for o in self._externOutputs:
            assert o.ctx is self._ctx, o

            for ep in tuple(o.endpoints):
                if ep in priv:
                    continue

                replacement = self._ioMap[o]._sig
                assert replacement.ctx is not self._ctx
                if isinstance(ep, HdlStatement):
                    ep._replace_input((o, replacement))

                elif isinstance(ep, HdlPortItem):
                    raise NotImplementedError(ep)

                else:
                    assert isinstance(ep, Operator), ep
                    # o.endpoints.remove(ep)
                    if ep in priv:
                        assert o not in ep.perands, (o, ep)
                        assert ep.result.ctx is self._ctx, ep
                    else:
                        # replace operand of the operator node
                        ep._replace_input(o, replacement)


def extractNetlistPartToSubunit(
                        inputs: UniqList[RtlSignal],
                        outputs: UniqList[RtlSignal],
                        priv: UniqList[Union[RtlSignal, Operator]]) -> ExtractedUnit:
    """
    :attention: extraction is executed on unit instantiation
    :attention: each object in priv must be reachable from inputs
    """
    privOutputs = []
    for o in outputs:
        inputs.discard(o)
        usedOnlyInternally = True
        for ep in o.endpoints:
            if ep not in priv:
                usedOnlyInternally = False
                break
        if usedOnlyInternally:
            privOutputs.append(o)
    
    for o in privOutputs:
        outputs.remove(o)

    for i in inputs:
        priv.discard(i)
    
    return ExtractedUnit(inputs, priv, outputs)        

        
def extractRegsToSubunit(regs: Sequence[RtlSyncSignal]) -> ExtractedUnit:
    # resolve IO
    inputs: UniqList[RtlSignal] = UniqList()
    outputs: UniqList[RtlSignal] = UniqList()
    priv: UniqList[Union[RtlSignal, Operator]] = UniqList()
    
    for r in regs:
        dffStm = r.singleDriver()._cut_off_drivers_of(r)
        dffNextStm = r.next.singleDriver()._cut_off_drivers_of(r.next)
        priv.extend((dffStm, dffNextStm))
    
        for stm in (dffStm, dffNextStm):
            for i in stm._inputs:
                consumeExpr(i, inputs, priv)
            outputs.extend(stm._outputs)
    
    return extractNetlistPartToSubunit(inputs, outputs, priv)

    
