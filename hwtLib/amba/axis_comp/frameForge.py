#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Optional, Union

from hwt.code import log2ceil, Switch, If, isPow2, SwitchLogic
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.frameTmplUtils import ChoicesOfFrameParts, StreamOfFramePars
from hwt.hdl.transPart import TransPart
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct, HStructField
from hwt.hdl.types.union import HUnion
from hwt.interfaces.std import Handshaked
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.unionIntf import UnionSink
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.byteOrder import reverseByteOrder
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.frameParser import AxiS_frameParser
from hwtLib.amba.axis_comp.templateBasedUnit import TemplateBasedUnit
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.streamNode import StreamNode, ExclusiveStreamGroups
from pyMathBitPrecise.bit_utils import mask


class AxiS_frameForge(AxiSCompBase, TemplateBasedUnit):
    """
    Assemble fields into frame on axi stream interface,
    frame description can be HType instance (HStruct, HUnion, ...)

    :note: if special frame format is required,
        it can be specified by TransTmpl instance and list of FrameTmpl
        (Input data structure can be splited into multiple frames as required)

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

    .. hwt-schematic:: _example_AxiS_frameForge
    """

    def __init__(self,
                 structT: HdlType,
                 tmpl: Optional[TransTmpl]=None,
                 frames: Optional[List[FrameTmpl]]=None):
        """
        :param hsIntfCls: class of interface which should be used
            as interface of this unit
        :param structT: instance of HStruct used as template for this frame
            If name is None no input port is generated and space
            is filled with invalid values, litle-endian encoding,
            supported types of interfaces are: Handshaked, Signal
            can be also instance of FrameTmpl
        :param tmpl: instance of TransTmpl for this structT
        :param frames: list of FrameTmpl instances for this tmpl
        :note: if tmpl and frames are None they are resolved
            from structT parseTemplate
        :note: This unit can parse sequence of frames,
            if they are specified by "frames"
        :note: structT can contain fields with variable size like HStream
        """
        self._structT = structT
        self._tmpl = tmpl
        self._frames = frames
        self._tmpRegsForSelect = {}

        AxiSCompBase.__init__(self)

    def _config(self):
        AxiSCompBase._config(self)
        self.USE_STRB = True

    @staticmethod
    def _mkFieldIntf(parent: StructIntf, structField: HStructField):
        """
        Instantiate interface for all members of input type
        """
        t = structField.dtype
        if isinstance(t, HUnion):
            return UnionSink(t, parent._instantiateFieldFn)
        elif isinstance(t, HStruct):
            return StructIntf(t, parent._instantiateFieldFn)
        elif isinstance(t, HStream):
            p = AxiStream()
            p.DATA_WIDTH = structField.dtype.element_t.bit_length()
            p.USE_STRB = True
            return p
        else:
            p = Handshaked()
            p.DATA_WIDTH = structField.dtype.bit_length()
            return p

    def _declr(self):
        """"
        Parse template and decorate with interfaces
        """
        self.parseTemplate()

        addClkRstn(self)
        with self._paramsShared():
            self.dataOut = self.intfCls()._m()

        if isinstance(self._structT, HStruct):
            intfCls = StructIntf
        elif isinstance(self._structT, HUnion):
            intfCls = UnionSink
        else:
            raise TypeError(self._structT)

        self.dataIn = intfCls(self._structT, self._mkFieldIntf)

    def connectPartsOfWord(self, wordData_out: RtlSignal,
                           tPart: Union[TransPart,
                                        ChoicesOfFrameParts,
                                        StreamOfFramePars],
                           inPorts_out: List[Union[Handshaked,
                                                   StreamNode]],
                           lastInPorts_out: List[Union[Handshaked,
                                                       StreamNode]]):
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
            parentIntf = tToIntf[tPart.origin.parent.origin]

            if parentIntf not in self._tmpRegsForSelect.keys():
                sel = HsBuilder(self, parentIntf._select).buff().end
                self._tmpRegsForSelect[parentIntf] = sel

            inPortGroups = ExclusiveStreamGroups()
            lastInPortsGroups = ExclusiveStreamGroups()

            # tuples (cond, part of data mux for dataOut)
            unionChoices = []

            # for all union choices
            for choice in tPart:
                tmp = self._sig("union_tmp_", Bits(w))
                intfOfChoice = tToIntf[choice.tmpl.origin]
                _, isSelected, isSelectValid = \
                    AxiS_frameParser.choiceIsSelected(self, intfOfChoice)
                unionChoices.append((isSelected, wordData_out[high:low](tmp)))

                isSelected = isSelected & isSelectValid

                inPortsNode = StreamNode()
                lastPortsNode = StreamNode()

                inPortGroups.append((isSelected, inPortsNode))
                lastInPortsGroups.append((isSelected, lastPortsNode))

                # walk all parts in union choice
                for _tPart in choice:
                    self.connectPartsOfWord(tmp, _tPart,
                                            inPortsNode.masters,
                                            lastPortsNode.masters)

            # generate data out mux
            SwitchLogic(unionChoices,
                        default=wordData_out(None))

            inPorts_out.append(inPortGroups)
            lastInPorts_out.append(lastInPortsGroups)
        elif isinstance(tPart, StreamOfFramePars):
            if len(tPart) != 1:
                raise NotImplementedError(
                    "Structuralized streams not implemented yiet")

            p = tPart[0]
            intf = tToIntf[p.tmpl.origin]

            if int(intf.DATA_WIDTH) != wordData_out._dtype.bit_length():
                raise NotImplementedError(
                    "Dynamic resizing of streams not implemented yiet")

            if len(self._frames) > 1:
                raise NotImplementedError(
                    "Dynamic splitting on frames not implemented yet")
            wordData_out(self.byteOrderCare(intf.data))
            inPorts_out.append(intf)

            if tPart.isLastPart():
                lastInPorts_out.append(intf)

            return intf.strb

        else:
            # connect parts of fields to output signal
            high, low = tPart.getBusWordBitRange()
            if tPart.isPadding:
                wordData_out[high:low](None)
            else:
                intf = tToIntf[tPart.tmpl.origin]
                fhigh, flow = tPart.getFieldBitRange()
                wordData_out[high:low](
                    self.byteOrderCare(intf.data)[fhigh:flow])
                inPorts_out.append(intf)

                if tPart.isLastPart():
                    lastInPorts_out.append(intf)

    def handshakeLogicForWord(self,
                              inPorts: List[Union[Handshaked, StreamNode]],
                              lastInPorts: List[Union[Handshaked, StreamNode]],
                              en: Union[bool, RtlSignal]):
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
        Frame specifier can contains unions/streams/padding/unaligned items
        and other features which makes code below complex.
        Frame specifier can also describe multiple frames.
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
        multipleWords = maxWordIndex > 0
        if multipleWords:
            # multiple word frame
            wordCntr_inversed = self._reg("wordCntr_inversed",
                                          Bits(log2ceil(maxWordIndex + 1),
                                               False),
                                          def_val=maxWordIndex)
            wcntrSw = Switch(wordCntr_inversed)

        # inversed indexes of ends of frames
        endsOfFrames = []
        extra_strbs = []
        for i, transParts, isLast in words:
            inversedIndx = maxWordIndex - i

            # input ports for value of this output word
            inPorts = []
            # input ports which value should be consumed on this word
            lastInPorts = []
            if multipleWords:
                wordData = self._sig("word%d" % i, dout.data._dtype)
            else:
                wordData = self.dataOut.data

            for tPart in transParts:
                extra_strb = self.connectPartsOfWord(
                    wordData, tPart,
                    inPorts,
                    lastInPorts)
                if extra_strb is not None:
                    if len(transParts) > 1:
                        raise NotImplementedError(
                            "Construct rest of the strb signal")
                    extra_strbs.append((inversedIndx, extra_strb))

            if multipleWords:
                en = wordCntr_inversed._eq(inversedIndx)
            else:
                en = True
            en = self.dataOut.ready & en

            ack = self.handshakeLogicForWord(inPorts, lastInPorts, en)

            inStreamLast = True
            for p in inPorts:
                if isinstance(p, AxiStream):
                    inStreamLast = p.last & inStreamLast

            if multipleWords:
                # word cntr next logic
                if i == maxWordIndex:
                    nextWordIndex = maxWordIndex
                else:
                    nextWordIndex = wordCntr_inversed - 1

                _ack = dout.ready & ack & inStreamLast

                a = [If(_ack,
                        wordCntr_inversed(nextWordIndex)
                        ),
                     ]
            else:
                a = []

            a.append(dout.valid(ack))

            # frame with multiple words (using wordCntr_inversed)
            if multipleWords:
                # data out logic
                a.append(dout.data(wordData))
                wcntrSw.Case(inversedIndx, a)

            # is last word in frame
            if isLast:
                endsOfFrames.append((inversedIndx, inStreamLast))

        # to prevent latches
        if not multipleWords:
            pass
        elif not isPow2(maxWordIndex + 1):
            default = wordCntr_inversed(maxWordIndex)
            default.append(dout.valid(0))
            default.append(dout.data(None))

            wcntrSw.Default(default)

        if multipleWords:
            last = False
            last_last = last
            for indexOrTuple in endsOfFrames:
                i, en = indexOrTuple
                last_last = wordCntr_inversed._eq(i) & en
                last = (last_last) | last

            selectRegLoad = last_last & dout.ready & ack
        else:
            last = endsOfFrames[0][1]
            selectRegLoad = dout.ready & ack

        for r in self._tmpRegsForSelect.values():
            r.rd(selectRegLoad)
        dout.last(last)

        strb = dout.strb
        STRB_ALL = mask(int(self.DATA_WIDTH // 8))
        if multipleWords:

            Switch(wordCntr_inversed).addCases([
                (i, strb(v)) for i, v in extra_strbs
            ]).Default(
                strb(STRB_ALL)
            )
        else:
            if extra_strbs:
                strb(extra_strbs[0][1])
            else:
                strb(STRB_ALL)


def _example_AxiS_frameForge():
    from hwtLib.types.ctypes import uint64_t, uint8_t, uint16_t

    t = HStruct((uint64_t, "item0"),
                (uint64_t, None),  # name = None means field is padding
                (uint64_t, "item1"),
                (uint8_t, "item2"), (uint8_t, "item3"), (uint16_t, "item4")
                )

    u = AxiS_frameForge(t)
    u.DATA_WIDTH = 32
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiS_frameForge()
    print(toRtl(u))
    # print(u._frames)
