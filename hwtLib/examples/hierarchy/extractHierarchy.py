#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from itertools import chain
from typing import Union, Optional, Sequence, Dict, Deque, List

from hwt.hdl.const import HConst
from hwt.hdl.operator import HOperatorNode
from hwt.hdl.operatorDefs import EVENT_OPS
from hwt.hdl.portItem import HdlPortItem
from hwt.hdl.statements.statement import HdlStatement
from hwt.hwIOs.std import HwIOClk, HwIORst, HwIORst_n, HwIOSignal
from hwt.pyUtils.setList import SetList
from hwt.hwModule import HwModule
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.rtlLevel.exceptions import SignalDriverErr
from hwtLib.abstract.componentBuilder import AbstractComponentBuilder


def consumeExpr(e: Union[RtlSignal, HConst],
                inputs:SetList[RtlSignal],
                seenObjs: SetList[Union[RtlSignal, HOperatorNode]]):
    """
    To make output code readable we must extract also expressions used in statements if they are private
    to selected statements.
    
    :note: Walk from endpoint to a driver. For every signal on path if all its endpoints are
        in seenObjs, add this to seenObjs and continue search on its drivers. 
    """
    if isinstance(e, HConst):
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
        assert isinstance(d, HOperatorNode), d
        d: HOperatorNode
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


class ExtractedHwModule(HwModule):
    """
    An unit which will extract selected circuit from parent on instantiation.
    """

    def __init__(self, externInputs: SetList[RtlSignal],
                  externObjsToExtract: SetList[Union[RtlSignal, HOperatorNode]],
                  externOutputs: SetList[RtlSignal],
                  hdlName:Optional[str]=None):
        HwModule.__init__(self, hdlName=hdlName)
        self._externInputs = externInputs
        self._externObjsToExtract = externObjsToExtract
        self._externOutputs = externOutputs

    def hwDeclr(self) -> None:
        ioMap = self._ioMap = {}
        for i in self._externInputs:
            i: RtlSignal
            hwIO = getattr(i, "_hwIO", None)
            iCloned = None
            if hwIO is not None:
                if isinstance(hwIO, (HwIOClk, HwIORst, HwIORst_n)):
                    iCloned = hwIO.__class__()
                    iCloned._updateHwParamsFrom(hwIO)

            if iCloned is None:
                iCloned = HwIOSignal(i._dtype)
            name = AbstractComponentBuilder(self, None, "")._findSuitableName(i._name, firstWithoutCntrSuffix=True)
            setattr(self, name, iCloned)
            assert i not in ioMap
            ioMap[i] = iCloned
        
        for o in self._externOutputs:
            o: RtlSignal
            oCloned = HwIOSignal(o._dtype)._m()
            name = AbstractComponentBuilder(self, None, "")._findSuitableName(o._name, firstWithoutCntrSuffix=True)
            setattr(self, name, oCloned)
            assert o not in ioMap
            ioMap[o] = oCloned

    def _handleUpdateForOutput(self, o: RtlSignal,
                               translation: Dict[RtlSignal, RtlSignal],
                               interOuts: Dict[RtlSignal, RtlSignal],
                               outerIoMap: Dict[RtlSignal, RtlSignal],
                               toTranslate: Deque[Union[HOperatorNode, HdlStatement, HdlPortItem]],
                               ):
        priv = self._externObjsToExtract

        translation[o] = o

        outerIo = outerIoMap.get(o, None)
        # drop operand cache items for expressions which will not be moved to this netlist
        # Must replace o with outerIo in every use of o outside of this unit
        assert o.ctx is self._ctx, o
        for ep in tuple(o.endpoints):
            if ep in priv:
                toTranslate.append(ep)
            else:
                assert outerIo is not None, (o, ep)
                if isinstance(ep, HdlStatement):
                    ep._replace_input((o, outerIo))
            
                elif isinstance(ep, HdlPortItem):
                    raise NotImplementedError(ep)
            
                else:
                    assert isinstance(ep, HOperatorNode), ep
                    if ep in priv:
                        assert o not in ep.perands, (o, ep)
                        assert ep.result.ctx is self._ctx, ep
                    else:
                        # replace operand of the operator node
                        ep._replace_input(o, outerIo)
        
        toDrop = []
        for k, v in o._usedOps.items():
            if isinstance(v, HConst):
                continue
            v: RtlSignal
            if v.ctx is self._ctx:
                continue
            try:
                d = v.singleDriver()
            except SignalDriverErr:
                raise NotImplementedError()
            # if d in priv:
            #    # will be moved later, we can keep it
            #    continue
            toDrop.append(k)

        for kToDrop in toDrop:
            o._usedOps.pop(kToDrop)
            o._usedOpsAlias.pop(kToDrop).remove(kToDrop)
        
        if outerIo is not None:
            interOuts[o](o)  # drive output of this unit

    def _moveOrCopyCircuitFromParent(self, translation: Dict[RtlSignal, RtlSignal],
                                     interOuts: Dict[RtlSignal, RtlSignal],
                                     outerIoMap: Dict[RtlSignal, RtlSignal]):
        # BFS move or copy circuit to this unit from parent
        priv = self._externObjsToExtract
        toTranslate: Deque[Union[HOperatorNode, HdlStatement, HdlPortItem]] = deque()
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
                ctx = self._parent._ctx
                assert stm in ctx.statements

                newInputs: Optional[List[Union[RtlSignal, HConst]]] = []
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
                
                for newI, i in zip(newInputs, stm._inputs):
                    if newI is not i:
                        stm._replace_input((i, newI))
                        
                for o in stm._outputs:
                    # move signal to a specified netlist
                    o.ctx.signals.remove(o)
                    o.ctx = self._ctx
                    o.ctx.signals.add(o)
                    self._handleUpdateForOutput(o, translation, interOuts, outerIoMap, toTranslate)

                ctx.statements.remove(stm)
                self._ctx.statements.add(stm)
                translation[stm] = stm
                stm._clean_signal_meta()

            elif isinstance(obj, HOperatorNode):
                shouldCopy = obj not in priv or obj.operator in EVENT_OPS
                if shouldCopy:
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
                            assert isinstance(op, HConst), op
                            newOps.append(op)
    
                    if newOps is None:
                        toTranslate.append(obj)
                        continue
                    # create a new copy of this object in this unit
                    newSig = obj.operator._evalFn(*newOps)
                    assert newSig.ctx is self._ctx, newSig
                    assert obj.result.ctx is not self._ctx, obj.result
                    
                else:
                    # move this object to his unit, move is done by translation of operand
                    # and by move is result signal to the netlist of this unit
                    # move signal to a specified netlist
                    o = obj.result
                    if o.ctx is not self._ctx:
                        o.ctx.signals.remove(o)
                        o.ctx = self._ctx
                        o.ctx.signals.add(o)
                    
                    translated = True
                    for op in tuple(obj.operands):
                        if isinstance(op, RtlSignal):
                            if op.ctx is self._ctx:
                                continue
                            _op = translation.get(op)
                            if _op is None:
                                # some input not available yet, must postpone translation
                                translated = False
                                break
                            else:
                                assert _op.ctx is self._ctx
                                obj._replace_input(op, _op)

                    if not translated:
                        toTranslate.append(obj)

                    self._handleUpdateForOutput(o, translation, interOuts, outerIoMap, toTranslate)
                    newSig = o

                translation[obj.result] = newSig
                translation[obj] = newSig.singleDriver()
                toTranslate.extend(ep for ep in obj.result.endpoints if ep in priv)
        
                outerIo = outerIoMap.get(obj.result, None)
                if outerIo is not None:
                    outerIo(newSig)
                
            else:
                raise NotImplementedError(obj.__class__, obj)

    def hwImpl(self) -> None:
        # transfer circuit to subunit
        # re-connect signals which should be connected to IO of new subunit
        translation = {i: self._ioMap[i]._sig for i in self._externInputs}
        interOuts = {i: self._ioMap[i]._sig for i in self._externOutputs}
        self._cleanThisSubunitRtlSignals()
        super(ExtractedHwModule, self)._signalsForSubHwModuleEntity(self._parent._ctx, "sig_" + self._name)
        
        outerIo = {i: self._ioMap[i]._sig for i in chain(self._externInputs, self._externOutputs)}
        self._moveOrCopyCircuitFromParent(translation, interOuts, outerIo)

        # connect external input signal to a input of this unit
        for i in self._externInputs:
            self._ioMap[i](i)
        self._outerIo = outerIo
        
    def _signalsForSubHwModuleEntity(self, context: RtlNetlist, prefix: str):
        assert context is self._parent._ctx, self
        assert prefix == "sig_" + self._name, (prefix, self._name) 
        for i in chain(self._externInputs, self._externOutputs):
            self._ioMap[i]._sig = self._outerIo[i]
    

def extractNetlistPartToSubmodule(
                        inputs: SetList[RtlSignal],
                        outputs: SetList[RtlSignal],
                        priv: SetList[Union[RtlSignal, HOperatorNode]]) -> ExtractedHwModule:
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
    
    return ExtractedHwModule(inputs, priv, outputs)        

        
def extractRegsToSubmodule(regs: Sequence[RtlSignal]) -> ExtractedHwModule:
    # resolve IO
    inputs: SetList[RtlSignal] = SetList()
    outputs: SetList[RtlSignal] = SetList()
    priv: SetList[Union[RtlSignal, HOperatorNode]] = SetList()
    
    for r in regs:
        dffStm = r.singleDriver()._cut_off_drivers_of(r)
        dffNextStm = r.next.singleDriver()._cut_off_drivers_of(r.next)
        priv.extend((dffStm, dffNextStm))
    
        for stm in (dffStm, dffNextStm):
            for i in stm._inputs:
                consumeExpr(i, inputs, priv)
            outputs.extend(stm._outputs)
    
    return extractNetlistPartToSubmodule(inputs, outputs, priv)
    
