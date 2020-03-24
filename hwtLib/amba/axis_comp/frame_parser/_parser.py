#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List, Union

from hwt.code import log2ceil, If, connect
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.typeShortcuts import hBit
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct, HStructField
from hwt.hdl.types.union import HUnion
from hwt.interfaces.std import Handshaked, Signal, VldSynced
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.unionIntf import UnionSource
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwtLib.abstract.template_configured import TemplateConfigured,\
    HdlType_separate
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.frame_parser.word_factory import WordFactory
from hwt.synthesizer.hObjList import HObjList
from hwtLib.amba.axis_comp.frame_parser.field_connector import AxiS_frameParserFieldConnector
from hwtLib.amba.axis_comp.frame_parser.footer_split import AxiS_footerSplit
from hwtLib.amba.axis_comp.frame_deparser.utils import drill_down_in_HStruct_fields
from hwt.code_utils import connect_optional
from hwtLib.amba.axis_comp.frame_join._join import AxiS_FrameJoin
from hwtLib.abstract.frame_utils.alignment_utils import FrameAlignmentUtils,\
    next_frame_offsets


def is_non_const_stream(t: HdlType):
    if isinstance(t, HStream):
        try:
            t.bit_length()
        except TypeError:
            return True

    return False


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

        t = self._structT
        if isinstance(t, HStruct):
            intfCls = StructIntf
        elif isinstance(t, HUnion):
            intfCls = UnionSource
        else:
            raise TypeError(t)

        self.dataOut = intfCls(t, self._mkFieldIntf)._m()

        with self._paramsShared():
            self.dataIn = self.intfCls()
            if self.SHARED_READY:
                self.dataOut_ready = Signal()
        self.parseTemplate()

    def parseTemplate(self):
        t = self._structT
        try:
            t.bit_length()
            is_const_size_frame = True
        except TypeError:
            is_const_size_frame = False

        if is_const_size_frame:
            self.sub_t = []
            self.children = []
            super(AxiS_frameParser, self).parseTemplate()
        else:
            if self._tmpl or self._frames:
                raise NotImplementedError()

            children = HObjList()
            self.sub_t = sub_t = []
            separated = list(HdlType_separate(t, is_non_const_stream))
            if len(separated) > 1 or separated[0][0]:
                # it may be required to delegate this on children
                for is_stream, s_t in separated:
                    if is_stream:
                        c = None
                    else:
                        c = self.__class__(s_t)
                    sub_t.append(s_t)
                    children.append(c)
                with self._paramsShared():
                    self.children = children

    def parser_fsm(self, words):
        din = self.dataIn
        maxWordIndex = words[-1][0]
        hasMultipleWords = maxWordIndex > 0
        if hasMultipleWords:
            wordIndex = self._reg("wordIndex", Bits(
                log2ceil(maxWordIndex + 1)), 0)
        else:
            wordIndex = None

        fc = AxiS_frameParserFieldConnector(self, self.dataIn, self.dataOut)
        allOutNodes = WordFactory(wordIndex)
        fc.connectParts(allOutNodes, words, wordIndex)

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

    def delegate_to_children(self):
        if self.SHARED_READY:
            raise NotImplementedError()
        assert len(self.sub_t) == len(self.children),\
            (self.sub_t, self.children)

        if len(self.children) == 2:
            c0, c1 = self.children
            t0, t1 = self.sub_t
            if c0 is None and isinstance(c1, self.__class__):
                fs = AxiS_footerSplit()
                fs._updateParamsFrom(self)
                fs.FOOTER_WIDTH = t1.bit_length()
                self.footer_split = fs
                fs.dataIn(self.dataIn)

                prefix_t, prefix = drill_down_in_HStruct_fields(t0, self.dataOut)
                assert isinstance(prefix_t, HStream), prefix_t
                prefix(fs.dataOut[0])
                footer_offsets = next_frame_offsets(prefix_t, self.DATA_WIDTH)
                footer = fs.dataOut[1]
                if footer_offsets != [0, ]:
                    # add aligment logic
                    align = AxiS_FrameJoin()
                    align._updateParamsFrom(self)
                    align.USE_KEEP = True
                    align.USE_STRB = False
                    align.OUT_OFFSET = 0
                    align.T = HStruct(
                        (HStream(t1, frame_len=1,
                                 start_offsets=[x // 8 for x in footer_offsets]), "f0"))
                    self.footer_align = align
                    connect(footer, align.dataIn[0], exclude=[footer.strb, align.dataIn[0].keep])
                    align.dataIn[0].keep(footer.strb)
                    footer = align.dataOut
                    connect(footer, c1.dataIn, exclude=[footer.keep, c1.dataIn.strb])
                    c1.dataIn.strb(footer.keep)
                else:
                    c1.dataIn(footer)
                connect_optional(c1.dataOut, self.dataOut)
            elif isinstance(c0, self.__class__) and c1 is None:
                raise NotImplementedError("prefix parser")
        else:
            raise NotImplementedError("multiple con-constant size segments")
        propagateClkRstn(self)

    def _impl(self):
        """
        Output data signals are directly connected to input in most of the cases,
        exceptions are:
        * Delayed parts of fields which were parsed in some previous input word
          for fields wich are crossing input word boundaries
        * Streams may have alignment logic if required
        """

        if self.sub_t:
            self.delegate_to_children()
        else:
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

    # t = HUnion(
    #     (HStruct(
    #         (uint64_t, "itemA0"),
    #         (uint64_t, "itemA1")
    #     ), "frameA"),
    #     (HStruct(
    #         (uint32_t, "itemB0"),
    #         (uint32_t, "itemB1"),
    #         (uint32_t, "itemB2"),
    #         (uint32_t, "itemB3")
    #     ), "frameB")
    # )
    t = HStruct(
        (HStream(uint8_t), "frame0"),
        (uint16_t, "footer")
    )

    u = AxiS_frameParser(t)
    u.USE_STRB = True
    u.DATA_WIDTH = 32
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiS_frameParser()

    print(toRtl(u))
