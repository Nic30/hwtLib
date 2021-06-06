#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List, Union

from hwt.code import If, Or
from hwt.code_utils import connect_optional, rename_signal
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct, HStructField
from hwt.hdl.types.union import HUnion
from hwt.hdl.types.utils import is_only_padding
from hwt.interfaces.std import Handshaked, Signal, VldSynced
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.unionIntf import UnionSource
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwtLib.abstract.frame_utils.alignment_utils import next_frame_offsets
from hwtLib.abstract.template_configured import TemplateConfigured, \
    HdlType_separate
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.frame_deparser.utils import drill_down_in_HStruct_fields
from hwtLib.amba.axis_comp.frame_join._join import AxiS_FrameJoin
from hwtLib.amba.axis_comp.frame_parser.field_connector import AxiS_frameParserFieldConnector
from hwtLib.amba.axis_comp.frame_parser.footer_split import AxiS_footerSplit
from hwtLib.amba.axis_comp.frame_parser.word_factory import WordFactory
from hwtLib.handshaked.streamNode import StreamNode
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


def is_non_const_stream(t: HdlType):
    if isinstance(t, HStream):
        try:
            t.bit_length()
        except TypeError:
            return True

    return False


def can_be_zero_sized(t: HdlType):
    while isinstance(t, HStruct) and len(t.fields) == 1:
        t = t.fields[0].dtype

    if isinstance(t, HStream):
        return t.len_min == 0
    return isinstance(t, HStruct) and not t.fields


class _AxiS_frameParserChildMeta():

    def __init__(self, t: HdlType, is_padding: bool, is_const_sized: bool):
        self.t = t
        self.is_padding = is_padding
        self.is_const_sized = is_const_sized
        self.can_be_zero_len = not is_const_sized and can_be_zero_sized(t)


def connect_with_clear(clear: RtlSignal, din: RtlSignal, dout: RtlSignal):
    If(clear,
       dout(0)
    ).Else(
       dout(din)
    )


@serializeParamsUniq
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

    :ivar ~.dataIn: the AxiStream interface for input frame
    :ivar ~.dataOut: output field interface generated from input type description
    :ivar ~.children: List[AxiS_frameParser] which contains a list of children components
        in the cases where this component works only as a wrapper of pipeline composed from actual parsers
    :ivar ~.children_meta: List[_AxiS_frameParserChildMeta] additional info for children list

    .. hwt-autodoc:: _example_AxiS_frameParser
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
        self.T = Param(self._structT)
        self.TRANSACTION_TEMPLATE = Param(self._tmpl)
        self.FRAME_TEMPLATES = Param(None if self._frames is None else tuple(self._frames))
        # if this is true field interfaces will be of type VldSynced
        # and single ready signal will be used for all
        # else every interface will be instance of Handshaked and it will
        # have it's own ready(rd) signal
        self.SHARED_READY = Param(False)
        # if true, a new state for overflow will be created in FSM
        self.OVERFLOW_SUPPORT = Param(False)
        # if True, a frame shorter than expected will cause the reset of main FSM
        self.UNDERFLOW_SUPPORT = Param(False)

    def _mkFieldIntf(self, parent: Union[StructIntf, UnionSource],
                     structField: HStructField):
        """
        Create an interface to export the data specified by the member of the structure
        """
        t = structField.dtype
        path = parent._field_path / structField.name
        if isinstance(t, HUnion):
            i = UnionSource(t, path, parent._instantiateFieldFn)
            i._fieldsToInterfaces = parent._fieldsToInterfaces
            return i
        elif isinstance(t, HStruct):
            i = StructIntf(t, path, parent._instantiateFieldFn)
            i._fieldsToInterfaces = parent._fieldsToInterfaces
            return i
        elif isinstance(t, HStream):
            if self.SHARED_READY:
                raise NotImplementedError("SHARED_READY=True and HStream field", structField)
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

        # input stream
        with self._paramsShared():
            self.dataIn = self.intfCls()
            if self.SHARED_READY:
                self.dataOut_ready = Signal()

        # parsed data
        if is_only_padding(t):
            self.dataOut = None
        else:
            self.dataOut = intfCls(t, tuple(), self._mkFieldIntf)._m()

        self.parseTemplate()
        if self.OVERFLOW_SUPPORT:
            # flag which is 1 if we are behind the data which
            # we described by type in configuration
            # :note: if the data is unaligned this may be 1 in last parsed word
            #        as well
            self.parsing_overflow: Signal = Signal()._m()

        if self.UNDERFLOW_SUPPORT:
            # flag which is 1 if the input stream ended prematurely
            # and main FSM will be restarted
            self.error_underflow: Signal = Signal()._m()

    def parseTemplate(self):
        """
        Load the configuration from the parameters
        """
        t = self._structT
        try:
            t.bit_length()
            is_const_size_frame = True
        except TypeError:
            is_const_size_frame = False

        self.children_meta: List[_AxiS_frameParserChildMeta] = []
        if is_const_size_frame:
            self.children = []
            super(AxiS_frameParser, self).parseTemplate()
        else:
            if self._tmpl or self._frames:
                raise NotImplementedError("Dynamic input size and the redefinition of the placement of fields in the data")

            children_meta = self.children_meta
            # try to cut the data type on const and variable size chunks
            # to simplify the parsing logic as these chunks can be handled
            # as usuall and only code specific to this case is handling of overlaps
            # of such a segments
            children = HObjList()
            separated = list(HdlType_separate(t, is_non_const_stream))
            if len(separated) > 1 or separated[0][0]:
                # it may be required to delegate this on children
                first = True
                for is_non_const_sized, s_t in separated:
                    _is_padding = is_only_padding(s_t)
                    if is_non_const_sized or (not first and _is_padding):
                        c = None
                    else:
                        c = self.__class__(s_t)

                    first = False
                    children.append(c)
                    cmeta = _AxiS_frameParserChildMeta(s_t, _is_padding, not is_non_const_sized)
                    children_meta.append(cmeta)

                if len(children_meta) >= 2 and \
                        children_meta[0].is_const_sized and\
                        not children_meta[1].is_const_sized:
                    # we will parse const-size prefix and
                    # then there will be a variable size suffix
                    children[0].OVERFLOW_SUPPORT = True

                with self._paramsShared(exclude=({"OVERFLOW_SUPPORT", "T"}, {})):
                    self.children = children

    def parser_fsm(self, words):
        din = self.dataIn
        maxWordIndex = words[-1][0]

        word_index_max_val = maxWordIndex
        if self.OVERFLOW_SUPPORT:
            word_index_max_val += 1
        hasMultipleWords = word_index_max_val > 0
        if hasMultipleWords:
            wordIndex = self._reg("wordIndex", Bits(
                log2ceil(word_index_max_val + 1)), 0)
        else:
            wordIndex = None

        allOutNodes = WordFactory(wordIndex)
        if not is_only_padding(self._structT):
            fc = AxiS_frameParserFieldConnector(self, self.dataIn, self.dataOut)
            fc.connectParts(allOutNodes, words, wordIndex)

        in_vld = din.valid
        if self.SHARED_READY:
            out_ready = self.dataOut_ready
            din.ready(out_ready)
        else:
            out_ready = self._sig("out_ready")
            out_ready(allOutNodes.ack())
            out_en = BIT.from_py(1)
            if self.OVERFLOW_SUPPORT:
                out_en = out_en & ~self.parsing_overflow
            allOutNodes.sync(out_en, in_vld)

        if self.OVERFLOW_SUPPORT:
            out_ready = out_ready | self.parsing_overflow
        din.ready(out_ready)

        if hasMultipleWords:
            incr = wordIndex(wordIndex + 1)
            data_ack = rename_signal(self, in_vld & out_ready, "data_ack")
            aligned = self._structT.bit_length() % self.DATA_WIDTH == 0

            if self.UNDERFLOW_SUPPORT:
                last = din.last
                self.error_underflow(data_ack & last & (
                    (wordIndex < maxWordIndex) if not aligned else wordIndex != maxWordIndex)
                )
            else:
                last = wordIndex._eq(maxWordIndex)

            if self.OVERFLOW_SUPPORT:
                last = din.last
                incr = If(wordIndex != word_index_max_val,
                   incr
                )
                if aligned:
                    overflow = wordIndex._eq(word_index_max_val)
                else:
                    overflow = wordIndex >= maxWordIndex

                self.parsing_overflow(overflow)

            If(data_ack,
                If(last,
                   wordIndex(0)
                ).Else(
                   incr
                )
            )

    def delegate_to_children(self):
        """
        After parsing task was split on some subtasks
        we are instantiating the child components to handle them
        and on this level we need to handle the synchronization between them
        """
        if self.SHARED_READY:
            raise NotImplementedError()
        assert len(self.children_meta) == len(self.children), \
            (self.children_meta, self.children)
        if self.OVERFLOW_SUPPORT:
            raise NotImplementedError()

        din = self.dataIn
        # :note: the children tasks are produced by disolving of original
        # parsed data type on const and non-const sized segments
        if len(self.children) == 2:
            c0, c1 = self.children
            cm0, cm1 = self.children_meta

            if not cm0.is_const_sized and cm1.is_const_sized:
                # suffix parser, split suffix and parse it in child sub component
                if cm0.can_be_zero_len:
                    assert self.USE_KEEP or self.USE_STRB, "keep or strb signal on AxiStream is required to mark 0 length packets"

                fs = AxiS_footerSplit()
                fs._updateParamsFrom(self)
                fs.FOOTER_WIDTH = cm1.t.bit_length()
                self.footer_split = fs

                fs.dataIn(din)

                prefix_t, prefix = drill_down_in_HStruct_fields(cm0.t, self.dataOut)
                if cm0.is_padding:
                    # padding
                    fs.dataOut[0].ready(1)
                else:
                    assert isinstance(prefix_t, HStream), prefix_t
                    prefix(fs.dataOut[0])

                suffix = fs.dataOut[1]
                if cm1.is_padding:
                    # ignore suffix entirely
                    suffix.ready(1)
                else:
                    # parse suffix in child component
                    suffix_offsets = next_frame_offsets(prefix_t, self.DATA_WIDTH)
                    if suffix_offsets != [0, ]:
                        # add aligment logic
                        align = AxiS_FrameJoin()
                        align._updateParamsFrom(
                            self,
                            exclude=({"T"}, {}))
                        align.USE_KEEP = True
                        align.USE_STRB = False
                        align.OUT_OFFSET = 0
                        align.T = HStruct(
                            (HStream(cm1.t, frame_len=1,
                                     start_offsets=[x // 8 for x in suffix_offsets]),
                             "f0"))
                        self.suffix_align = align
                        align.dataIn[0](suffix, exclude=[suffix.strb, align.dataIn[0].keep])
                        align.dataIn[0].keep(suffix.strb)
                        suffix = align.dataOut
                        c1.dataIn(suffix, exclude=[suffix.keep,
                                                   c1.dataIn.strb])
                        c1.dataIn.strb(suffix.keep)
                    else:
                        c1.dataIn(suffix)

                if not cm1.is_padding:
                    connect_optional(c1.dataOut, self.dataOut)

            elif cm0.is_const_sized and not cm1.is_const_sized:
                # prefix parser, parser prefix in subcomponent
                # and let rest to a suffix
                if not cm0.is_padding:
                    connect_optional(c0.dataOut, self.dataOut)
                masters = [din]
                if cm1.is_padding:
                    slaves = [c0.dataIn, ]
                    extraConds = None
                    skipWhen = None
                else:
                    suffix_t, suffix = drill_down_in_HStruct_fields(cm1.t, self.dataOut)
                    assert isinstance(suffix_t, HStream), suffix_t
                    t1_offset = c0._structT.bit_length() % self.DATA_WIDTH
                    if t1_offset == 0:
                        slaves = [c0.dataIn, suffix]
                        if cm1.can_be_zero_len:
                            assert suffix.USE_KEEP or suffix.USE_STRB, "keep or strb signal on AxiStream is required to mark 0 length packets"
                            is_zero_len = ~c0.parsing_overflow & din.valid & din.last
                            # this is a stream after some header, we need to assert that we
                            # output the 0B packet (valid=1, ready=1, last=1, keep=0) at the end
                            extraConds = {
                               # c0.dataIn:~c0.parsing_overflow,
                               suffix: c0.parsing_overflow | (din.valid & din.last),
                            }
                            skipWhen = {
                               suffix:~c0.parsing_overflow & ~(din.valid & din.last),
                            }
                            controll_signals = [din.valid, din.ready]
                            if suffix.USE_KEEP:
                                controll_signals.append(suffix.keep)
                                connect_with_clear(is_zero_len, din.keep, suffix.keep)
                            if suffix.USE_STRB:
                                controll_signals.append(suffix.strb)
                                connect_with_clear(is_zero_len, din.strb, suffix.strb)

                            suffix(din, exclude=controll_signals)

                        else:
                            # t1 is aligned on word boundary
                            # and does not require any first word mask modification

                            # We enable the input to c1 once the c0 is finished with the parsing (parsing_overflow=1)
                            extraConds = {
                               # c0.dataIn:~c0.parsing_overflow,
                               suffix: c0.parsing_overflow,
                            }
                            skipWhen = {
                               suffix:~c0.parsing_overflow,
                            }
                            suffix(din, exclude=[din.valid, din.ready])

                    else:
                        raise NotImplementedError("prefix parser- modify mask for suffix first word")

                StreamNode(masters, slaves,
                           extraConds=extraConds,
                           skipWhen=skipWhen).sync()
                c0.dataIn(din, exclude=[din.valid, din.ready])
            else:
                raise NotImplementedError("multiple(2) non-constant size segments in parsed datastructure, do parse frame incrementally instead")
        else:
            raise NotImplementedError("multiple non-constant size segments in parsed datastructure, do parse frame incrementally instead")
        if self.UNDERFLOW_SUPPORT:
            self.error_underflow(Or(*(c.error_underflow for c in self.children if c is not None)))

        propagateClkRstn(self)

    def _impl(self):
        """
        Output data signals are directly connected to input in most of the cases,
        exceptions are:

        * Delayed parts of fields which were parsed in some previous input word
          for fields wich are crossing input word boundaries
        * Streams may have alignment logic if required
        """

        if self.children_meta:
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
    # t = HUnion(
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
        (HStream(uint8_t, frame_len=(0, 1)), "frame0"),
        (uint16_t, "footer")
    )

    u = AxiS_frameParser(t)
    u.USE_STRB = True
    u.DATA_WIDTH = 32
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_AxiS_frameParser()

    print(to_rtl_str(u))
