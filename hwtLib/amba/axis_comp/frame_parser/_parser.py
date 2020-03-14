#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List, Union

from hwt.code import log2ceil, If, Concat, connect, Switch
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.frameTmplUtils import ChoicesOfFrameParts
from hwt.hdl.transPart import TransPart
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.typeShortcuts import hBit
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct, HStructField
from hwt.hdl.types.union import HUnion
from hwt.interfaces.std import Handshaked, Signal, VldSynced
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.unionIntf import UnionSource, UnionSink
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.byteOrder import reverseByteOrder
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.abstract.template_configured import TemplateConfigured
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.frame_parser.out_containers import ListOfOutNodeInfos, \
    ExclusieveListOfHsNodes, InNodeInfo, InNodeReadOnlyInfo, OutNodeInfo, \
    OutStreamNodeInfo, OutStreamNodeGroup
from hwtLib.amba.axis_comp.frame_parser.word_factory import WordFactory
from hwtLib.handshaked.builder import HsBuilder
from pyMathBitPrecise.bit_utils import mask


class AxiS_frameParser(AxiSCompBase, TemplateConfigured):
    """
    Parse frame specified by HType (HStruct, HUnion, ...) into fields

    :note: if special frame format is required,
        it can be specified by TransTmpl instance and list of FrameTmpl
        (Output data structure can be splited into multiple frames as required)

    .. aafig::
                                      +---------+
                              +------>| field0  |
                              |       +---------+
                      +-------+-+
         input stream |         |     +---------+
        +-------------> parser  +---->| field1  |
                      |         |     +---------+
                      +-------+-+
                              |       +---------+
                              +------>| field2  |
                                      +---------+

    :note: names in the figure are just illustrative

    :ivar dataIn: the AxiStream interface for input frame
    :ivar dataOut: output field interface generated from input type description

    .. hwt-schematic:: _example_AxiS_frameParser
    """

    def __init__(self, structT: HdlType,
                 tmpl: Optional[TransTmpl]=None,
                 frames: Optional[List[FrameTmpl]]=None):
        """
        :param structT: instance of HStruct which specifies
            data format to download
        :param tmpl: instance of TransTmpl for this structT
        :param frames: list of FrameTmpl instances for this tmpl
        :note: if tmpl and frames are None they are resolved
            from structT parseTemplate
        :note: this unit can parse sequence of frames,
            if they are specified by "frames"
        :attention: structT can not contain fields with variable size
            like HStream
        """
        TemplateConfigured.__init__(self, structT, tmpl, frames)
        AxiSCompBase.__init__(self)

    def _config(self):
        self.intfCls._config(self)
        # if this is true field interfaces will be of type VldSynced
        # and single ready signal will be used for all
        # else every interface will be instance of Handshaked and it will
        # have it's own ready(rd) signal
        self.SHARED_READY = Param(False)

    def _mkFieldIntf(self, parent: Union[StructIntf, UnionSource],
                     structField: HStructField):
        t = structField.dtype
        if isinstance(t, HUnion):
            return UnionSource(t, parent._instantiateFieldFn)
        elif isinstance(t, HStruct):
            return StructIntf(t, parent._instantiateFieldFn)
        elif isinstance(t, HStream):
            if self.SHARED_READY:
                raise NotImplementedError(t)
            else:
                i = AxiStream()
                i._updateParamsFrom(self)
                return i
        else:
            if self.SHARED_READY:
                i = VldSynced()
            else:
                i = Handshaked()
            i.DATA_WIDTH = structField.dtype.bit_length()
            return i

    def _declr(self):
        if self.ID_WIDTH:
            raise NotImplementedError(self.ID_WIDTH)
        if self.DEST_WIDTH:
            raise NotImplementedError(self.DEST_WIDTH)

        addClkRstn(self)

        if isinstance(self._structT, HStruct):
            intfCls = StructIntf
        elif isinstance(self._structT, HUnion):
            intfCls = UnionSource
        else:
            raise TypeError(self._structT)

        self.dataOut = intfCls(self._structT, self._mkFieldIntf)._m()

        with self._paramsShared():
            self.dataIn = self.intfCls()
            if self.SHARED_READY:
                self.dataOut_ready = Signal()

    def getInDataSignal(self, transPart: TransPart):
        busDataSignal = self.dataIn.data
        high, low = transPart.getBusWordBitRange()
        return busDataSignal[high:low]

    def choiceIsSelected(self,
                         interfaceOfChoice: Union[UnionSource, UnionSink]):
        """
        Check if union member is selected by _select interface
        in union interface
        """
        parent = interfaceOfChoice._parent
        r = self._tmpRegsForSelect[parent]
        i = parent._interfaces.index(interfaceOfChoice)
        return i, r.data._eq(i), r.vld

    def connectParts(self,
                     allOutNodes: ListOfOutNodeInfos,
                     words,
                     wordIndex: Optional[RtlSignal]):
        """
        Create main datamux from dataIn to dataOut
        """
        for currentWordIndex, transParts, _ in words:
            # each word index is used and there may be TransParts which are
            # representation of padding
            outNondes = ListOfOutNodeInfos()
            for part in transParts:
                self.connectPart(outNondes, part, hBit(1), hBit(1),
                                 wordIndex, currentWordIndex)

            allOutNodes.addWord(currentWordIndex, outNondes)

    def connectChoicesOfFrameParts(
            self,
            hsNondes: ListOfOutNodeInfos,
            part: ChoicesOfFrameParts,
            en: Union[RtlSignal, bool],
            exclusiveEn: Optional[RtlSignal],
            wordIndex: Optional[RtlSignal],
            currentWordIndex: int):
        tToIntf = self.dataOut._fieldsToInterfaces
        parentIntf = tToIntf[part.origin.parent.origin]
        try:
            sel = self._tmpRegsForSelect[parentIntf]
        except KeyError:
            sel = HsBuilder(self, parentIntf._select).buff().end
            self._tmpRegsForSelect[parentIntf] = sel
        unionGroup = ExclusieveListOfHsNodes(sel)

        # for unions
        for choice in part:
            # connect data signals of choices and collect info about
            # streams
            intfOfChoice = tToIntf[choice.tmpl.origin]
            selIndex, isSelected, isSelectValid = self.choiceIsSelected(
                intfOfChoice)
            _exclusiveEn = isSelectValid & isSelected & exclusiveEn

            unionMemberPart = ListOfOutNodeInfos()
            for p in choice:
                self.connectPart(unionMemberPart, p, en, _exclusiveEn,
                                 wordIndex, currentWordIndex)
            unionGroup.append(selIndex, unionMemberPart)
        hsNondes.append(unionGroup)

        if wordIndex is not None:
            en = en & wordIndex._eq(currentWordIndex)
        if part.isLastPart():
            # synchronization of reading from _select register for unions
            selNode = InNodeInfo(sel, en)
        else:
            selNode = InNodeReadOnlyInfo(sel, en)
        hsNondes.append(selNode)

    def connectStreamOfFrameParts(
            self,
            hsNondes: ListOfOutNodeInfos,
            part: Union[TransPart, ChoicesOfFrameParts],
            en: Union[RtlSignal, bool],
            exclusiveEn: Optional[RtlSignal],
            wordIndex: Optional[RtlSignal],
            currentWordIndex: int):
        orig = part.tmpl.origin
        dout = self.dataOut._fieldsToInterfaces[orig]
        if isinstance(orig, HStructField):
            orig = orig.dtype
        assert isinstance(orig, HStream), orig

        #if not part.isLastPart():
        #    raise NotImplementedError()

        if not len(orig.start_offsets) == 1:
            raise NotImplementedError()

        din = self.dataIn
        is_first_part_in_stream = part.tmpl.parent.bitAddr == part.startOfPart
        if is_first_part_in_stream:
            frame_range = part.tmpl.parent.bitAddr, part.tmpl.parent.bitAddrEnd
            DW = self.DATA_WIDTH
            start_offset = frame_range[0] % DW
            end_rem = frame_range[1] % DW
            if orig.start_offsets != [0, ]:
                raise NotImplementedError()

            # this is a first part of stream
            # now connect all data for each part
            non_data_signals = [din.valid, din.ready, din.last]
            if start_offset == 0 and end_rem == 0:
                pass
            else:
                if dout.USE_STRB:
                    non_data_signals.append(din.strb)
                if dout.USE_KEEP:
                    non_data_signals.append(din.keep)

                assert start_offset % 8 == 0, start_offset
                assert end_rem % 8 == 0, end_rem
                first_word_i = frame_range[0] // DW
                last_word_i = (frame_range[1] - 1) // DW
                first_word_mask = mask((DW - start_offset) // 8) << start_offset // 8
                body_word_mask = mask(DW//8)
                def set_mask(m):
                    res = []
                    if dout.USE_STRB:
                        res.append(dout.strb(m))
                    if dout.USE_KEEP:
                        res.append(dout.keep(m))
                    return res

                if end_rem == 0:
                    last_word_mask = body_word_mask
                else:
                    last_word_mask = mask(end_rem//8)
                if first_word_i == last_word_i:
                    # only single word, mask is constant
                    m = first_word_mask & last_word_mask
                    set_mask(m)
                elif first_word_i == last_word_i + 1:
                    # only two words, mask is differnt between word 0 and 1
                    raise NotImplementedError()
                else:
                    # 2+ words, first and body or last and body may be same
                    if first_word_mask == body_word_mask:
                        # last is only word with a special mask
                        If(wordIndex._eq(last_word_i),
                            *set_mask(last_word_mask)
                        ).Else(
                            *set_mask(body_word_mask)
                        )
                    elif last_word_mask == body_word_mask:
                        # first is only word with special mask
                        If(wordIndex._eq(first_word_i),
                            *set_mask(first_word_mask)
                        ).Else(
                            *set_mask(body_word_mask)
                        )
                    else:
                        # first, last, body word have all unique masks
                        Switch(wordIndex)\
                        .Case(first_word_i, set_mask(first_word_mask))\
                        .Case(last_word_i, set_mask(last_word_mask))\
                        .Default(set_mask(body_word_mask))

            connect(din, dout, exclude=non_data_signals)
        is_last_part_in_stream = part.tmpl.parent.bitAddrEnd == part.endOfPart
        if is_last_part_in_stream:
            if wordIndex is None:
                last = 1
            else:
                last = wordIndex._eq(currentWordIndex)
            dout.last(last)

        if is_first_part_in_stream or part.startOfPart % self.DATA_WIDTH == 0:
            # first part in current word
            streamGroup = self._streamNodes.setdefault(dout, OutStreamNodeGroup(wordIndex, currentWordIndex))
            streamGroup.word_range_max = currentWordIndex
            on = OutStreamNodeInfo(self, dout, en, exclusiveEn, streamGroup)
            hsNondes.append(on)

    def connectPart(self,
                    hsNondes: ListOfOutNodeInfos,
                    part: Union[TransPart, ChoicesOfFrameParts],
                    en: Union[RtlSignal, bool],
                    exclusiveEn: Union[RtlSignal, bool],
                    wordIndex: Optional[RtlSignal],
                    currentWordIndex: int):
        """
        Create datamux for a single output word in main fsm
        and colect metainformations for handshake logic
        and strb/keep

        :param hsNondes: list of nodes of handshaked logic
        """
        if isinstance(part, ChoicesOfFrameParts):
            # connect union field
            return self.connectChoicesOfFrameParts(
                hsNondes, part, en, exclusiveEn, wordIndex, currentWordIndex)
        # elif isinstance(part, StreamOfFrameParts):
        #     return self.connectStreamOfFrameParts(
        #                hsNondes, part, en, exclusiveEn, wordIndex)
        elif part.isPadding:
            return

        fieldInfo = part.tmpl.origin
        if isinstance(fieldInfo, HStream) or (
                isinstance(fieldInfo, HStructField) and
                isinstance(fieldInfo.dtype, HStream)):
            return self.connectStreamOfFrameParts(
                hsNondes, part, en, exclusiveEn, wordIndex, currentWordIndex)

        # connect regular scalar field
        fPartSig = self.getInDataSignal(part)
        assert isinstance(fieldInfo, HStructField), fieldInfo

        try:
            signalsOfParts = self._signalsOfParts[part.tmpl]
        except KeyError:
            signalsOfParts = []
            self._signalsOfParts[part.tmpl] = signalsOfParts

        if wordIndex is not None:
            en = en & wordIndex._eq(currentWordIndex)

        if part.isLastPart():
            # connect all parts in this group to output stream
            signalsOfParts.append(fPartSig)
            tToIntf = self.dataOut._fieldsToInterfaces
            intf = tToIntf[fieldInfo]
            intf.data(self.byteOrderCare(
                Concat(
                    *reversed(signalsOfParts)
                ))
            )
            on = OutNodeInfo(self, intf, en, exclusiveEn)
            hsNondes.append(on)
        else:
            # part is not in same word as last part, we have to store it's value
            # to register until the last part arrive
            fPartReg = self._reg("%s_part_%d" % (
                    fieldInfo.name,
                    len(signalsOfParts)),
                fPartSig._dtype)
            dataVld = self.dataIn.valid & en & exclusiveEn
            If(dataVld,
               fPartReg(fPartSig)
            )
            signalsOfParts.append(fPartReg)

    def parser_fsm(self, words):
        din = self.dataIn
        maxWordIndex = words[-1][0]
        hasMultipleWords = maxWordIndex > 0
        if hasMultipleWords:
            wordIndex = self._reg("wordIndex", Bits(
                log2ceil(maxWordIndex + 1)), 0)
        else:
            wordIndex = None

        if self.IS_BIGENDIAN:
            byteOrderCare = reverseByteOrder
        else:
            def byteOrderCare(sig):
                return sig

        self.byteOrderCare = byteOrderCare
        self._tmpRegsForSelect = {}
        # TransTmpl: List[RtlSignal]
        self._signalsOfParts = {}
        # AxiStream: OutStreamNodeInfo
        self._streamNodes = {}

        allOutNodes = WordFactory(wordIndex)
        self.connectParts(allOutNodes, words, wordIndex)

        in_vld = din.valid
        if self.SHARED_READY:
            out_ready = self.dataOut_ready
            din.ready(out_ready)
        else:
            out_ready = self._sig("out_ready")
            out_ready(allOutNodes.ack())
            allOutNodes.sync(hBit(1), in_vld)

        din.ready(out_ready)

        if hasMultipleWords:
            last = wordIndex._eq(maxWordIndex)

            If(in_vld & out_ready,
                If(last,
                   wordIndex(0)
                ).Else(
                    wordIndex(wordIndex + 1)
                )
            )

    def _impl(self):
        """
        Output data signals are directly connected to input in most of the cases,
        exceptions are:
        * Delayed parts of fields which were parsed in some previous input word
          for fields wich are crossing input word boundaries
        * Streams may have alignment logic if required
        """
        self.parseTemplate()
        words = list(self.chainFrameWords())
        self.parser_fsm(words)


def _example_AxiS_frameParser():
    from hwtLib.types.ctypes import uint8_t, uint16_t, uint32_t, uint64_t
    # t = HStruct(
    #  (uint64_t, "item0"),  # tuples (type, name) where type has to be instance of Bits type
    #  (uint64_t, None),  # name = None means this field will be ignored
    #  (uint64_t, "item1"),
    #  (uint64_t, None),
    #  (uint16_t, "item2"),
    #  (uint16_t, "item3"),
    #  (uint32_t, "item4"),
    #  (uint32_t, None),
    #  (uint64_t, "item5"),  # this word is split on two bus words
    #  (uint32_t, None),
    #  (uint64_t, None),
    #  (uint64_t, None),
    #  (uint64_t, None),
    #  (uint64_t, "item6"),
    #  (uint64_t, "item7"),
    #  (HStruct(
    #      (uint64_t, "item0"),
    #      (uint64_t, "item1"),
    #   ),
    #   "struct0")
    #  )
    #t = HUnion(
    #   (uint32_t, "a"),
    #   (uint32_t, "b")
    #   )

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
    #t = HStruct(
    #    (HStream(uint8_t, frame_len=5), "frame0"),
    #    (uint16_t, "footer")
    #)

    u = AxiS_frameParser(t)
    u.DATA_WIDTH = 64
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiS_frameParser()

    print(toRtl(u))
