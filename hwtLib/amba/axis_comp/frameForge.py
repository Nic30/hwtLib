#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Dict, Optional, Union

from hwt.bitmask import mask
from hwt.code import log2ceil, Switch, If, isPow2, In, SwitchLogic
from hwt.hdlObjects.frameTmplUtils import ChoicesOfFrameParts
from hwt.hdlObjects.types.bits import Bits
from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.types.union import HUnion
from hwt.interfaces.std import Handshaked
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.unionIntf import UnionSink
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.byteOrder import reverseByteOrder
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.templateBasedUnit import TemplateBasedUnit
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.streamNode import StreamNode, ExclusiveStreamGroups


class AxiS_frameForge(AxiSCompBase, TemplateBasedUnit):
    """
    Assemble fields into frame on axi stream interface

    :note: names in the picture are just illustrative

    .. aafig::
        +---------+
        | field0  +------+
        +---------+      |
                       +-v-------+
        +---------+    |         | output stream
        | field1  +---->  forge  +--------------->
        +---------+    |         |
                       +-^-------+
        +---------+      |
        | field2  +------+
        +---------+
    """
    def __init__(self, axiSIntfCls, structT,
                 tmpl=None, frames=None):
        """
        :param hsIntfCls: class of interface which should be used as interface of this unit
        :param structT: instance of HStruct used as template for this frame
            if name is None no input port is generated and space is filled with invalid values
            litle-endian encoding,
            supported types of interfaces are: Handshaked, Signal
            can be also instance of FrameTmpl
        :param tmpl: instance of TransTmpl for this structT
        :param frames: list of FrameTmpl instances for this tmpl
        :note: if tmpl and frames are None they are resolved from structT parseTemplate
        :note: this unit can parse sequence of frames, if they are specified by "frames"
        :note: structT can contain fields with variable size like HStream
        """
        if axiSIntfCls is not AxiStream:
            raise NotImplementedError()

        self._structT = structT
        self._tmpl = tmpl
        self._frames = frames
        self._tmpRegsForSelect = {}

        AxiSCompBase.__init__(self, axiSIntfCls)

    @staticmethod
    def _mkFieldIntf(parent, structField):
        """
        Instantiate interface for all members of input type
        """
        t = structField.dtype
        if isinstance(t, HUnion):
            return UnionSink(t, parent._instantiateFieldFn)
        elif isinstance(t, HStruct):
            return StructIntf(t, parent._instantiateFieldFn)
        else:
            p = Handshaked()
            p.DATA_WIDTH.set(structField.dtype.bit_length())
            return p

    def _declr(self):
        """"
        Parse template and decorate with interfaces
        """
        self.parseTemplate()

        addClkRstn(self)
        with self._paramsShared():
            self.dataOut = self.intfCls()

        if isinstance(self._structT, HStruct):
            intfCls = StructIntf
        elif isinstance(self._structT, HUnion):
            intfCls = UnionSink
        else:
            raise TypeError(self._structT)

        self.dataIn = intfCls(self._structT, self._mkFieldIntf)

    def choiceIsSelected(self, interfaceOfChoice):
        """
        Check if union member is selected by _select interface in union interface
        """
        parent = interfaceOfChoice._parent
        try:
            r = self._tmpRegsForSelect[parent]
        except KeyError:
            r = HsBuilder(self, parent._select).buff().end
            self._tmpRegsForSelect[parent] = r

        i = parent._interfaces.index(interfaceOfChoice)
        return r.data._eq(i), r.vld

    def connectPartsOfWord(self, wordData_out: RtlSignal,
                           tPart, inPorts_out, lastInPorts_out: List[Interface]):
        """
        Connect transactions parts to signal for word of output stream

        :param wordData_out: signal for word of output stream
        :param tPart: instance of TransPart or ChoicesOfFrameParts to connect
        :param inPorts_out: input interfaces to this transaction part
        :param lastInPorts_out: input interfaces for last parts of transactions
        """

        tToIntf = self.dataIn._fieldsToInterfaces

        if isinstance(tPart, ChoicesOfFrameParts):
            # connnect parts of union to output signal
            w = tPart.bit_length()
            high, low = tPart.getBusWordBitRange()

            inPortGroups = ExclusiveStreamGroups()
            lastInPortsGroups = ExclusiveStreamGroups()
            unionChoices = []

            for choice in tPart:
                tmp = self._sig("union_tmp_", Bits(w))
                intfOfChoice = tToIntf[choice.tmpl.origin]
                isSelected, isSelectValid = self.choiceIsSelected(intfOfChoice)
                unionChoices.append((isSelected, wordData_out[high:low] ** tmp))

                isSelected = isSelected & isSelectValid

                inPortsNode = StreamNode()
                lastPortsNode = StreamNode()

                inPortGroups.append((isSelected, inPortsNode))
                lastInPortsGroups.append((isSelected, lastPortsNode))

                for _tPart in choice:
                    self.connectPartsOfWord(tmp, _tPart,
                                            inPortsNode.masters,
                                            lastPortsNode.masters)

            SwitchLogic(unionChoices,
                        default=wordData_out ** None)

            inPorts_out.append(inPortGroups)
            lastInPorts_out.append(lastInPortsGroups)

        else:
            # connect parts of fields to output signal
            high, low = tPart.getBusWordBitRange()
            if tPart.isPadding:
                wordData_out[high:low] ** None
            else:
                intf = tToIntf[tPart.tmpl.origin]
                fhigh, flow = tPart.getFieldBitRange()
                wordData_out[high:low] ** self.byteOrderCare(intf.data)[fhigh:flow]
                inPorts_out.append(intf)

                if tPart.isLastPart():
                    lastInPorts_out.append(intf)

    def handshakeLogicForWord(self, lastInPorts, en, inPorts):
        if lastInPorts:
            # instantiate rd logic of input streams
            StreamNode(masters=lastInPorts).sync(en)

        if inPorts:
            ack = StreamNode(masters=inPorts).ack()
        else:
            ack = True

        return ack

    def _impl(self):
        """
        Iterate over words in template and create stream output mux and fsm.
        """
        if self.IS_BIGENDIAN:
            byteOrderCare = reverseByteOrder
        else:
            def byteOrderCare(sig):
                return sig
        self.byteOrderCare = byteOrderCare

        words = list(self.chainFrameWords())
        dout = self.dataOut
        self.parseTemplate()
        maxWordIndex = words[-1][0]
        useCounter = maxWordIndex > 0
        if useCounter:
            # multiple word frame
            wordCntr_inversed = self._reg("wordCntr_inversed",
                                          Bits(log2ceil(maxWordIndex + 1), False),
                                          defVal=maxWordIndex)
            wcntrSw = Switch(wordCntr_inversed)

        endsOfFrames = []
        for i, transParts, isLast in words:
            inversedIndx = maxWordIndex - i

            inPorts = []
            lastInPorts = []
            wordData = self._sig("word%d" % i, dout.data._dtype)

            for tPart in transParts:
                self.connectPartsOfWord(wordData, tPart,
                                        inPorts,
                                        lastInPorts)

            if useCounter:
                en = wordCntr_inversed._eq(inversedIndx)
            else:
                en = True
            en = self.dataOut.ready & en
            ack = self.handshakeLogicForWord(lastInPorts, en, inPorts)
            if useCounter:
                # word cntr next logic
                if i == maxWordIndex:
                    nextWordIndex = maxWordIndex
                else:
                    nextWordIndex = wordCntr_inversed - 1

                if ack is True:
                    _ack = dout.ready
                else:
                    _ack = dout.ready & ack

                a = If(_ack,
                       wordCntr_inversed ** nextWordIndex
                    )
            else:
                a = []

            a.extend(dout.valid ** ack)
            # data out logic
            a.extend(dout.data ** wordData)

            if useCounter:
                wcntrSw.Case(inversedIndx, a)

            if isLast:
                endsOfFrames.append(inversedIndx)

        # to prevent latches
        if not useCounter:
            pass
        elif not isPow2(maxWordIndex + 1):
            default = wordCntr_inversed ** maxWordIndex
            default.extend(dout.valid ** 0)
            default.extend(dout.data ** None)

            wcntrSw.Default(default)

        if useCounter:
            dout.last ** In(wordCntr_inversed, endsOfFrames)
            for r in self._tmpRegsForSelect.values():
                r.rd ** (ack & wordCntr_inversed._eq(endsOfFrames[-1]))

        else:
            dout.last ** 1
            for r in self._tmpRegsForSelect.values():
                r.rd ** ack

        dout.strb ** mask(int(self.DATA_WIDTH // 8))


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.types.ctypes import uint64_t, uint32_t, int32_t, uint8_t, uint16_t
    #t = unionSimple = HUnion(
    #    (uint32_t, "a"),
    #    (int32_t, "b")
    #    )
    t = HUnion(
           (HStruct(
               (uint64_t, "itemA0"),
               (uint64_t, "itemA1")
               ), "frameA"),
           (HStruct(
               (uint32_t, "itemB0"),
               (uint32_t, "itemB1"),
               (uint32_t, "itemB2"),
               (uint32_t, "itemB3")
               ), "frameB")
           )
    #t = HStruct((uint64_t, "item0"),
    #           (uint64_t, None),  # name = None means field is padding
    #           (uint64_t, "item1"),
    #           (uint8_t, "item2"), (uint8_t, "item3"), (uint16_t, "item4")
    #           )
    u = AxiS_frameForge(AxiStream, t)
    u.DATA_WIDTH.set(64)
    print(toRtl(u))
    # print(u._frames)
