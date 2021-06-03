#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Optional, Union, Tuple

from hwt.code import Switch, If, SwitchLogic
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.frameTmplUtils import ChoicesOfFrameParts
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
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil, isPow2
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.abstract.template_configured import TemplateConfigured, \
    separate_streams, to_primitive_stream_t
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.frame_deparser.strb_keep_stash import StrbKeepStash, \
    reduce_conditional_StrbKeepStashes
from hwtLib.amba.axis_comp.frame_deparser.utils import _get_only_stream, \
    connect_optional_with_best_effort_axis_mask_propagation, \
    drill_down_in_HStruct_fields
from hwtLib.amba.axis_comp.frame_join import AxiS_FrameJoin
from hwtLib.amba.axis_comp.frame_parser.field_connector import AxiS_frameParserFieldConnector, \
    get_byte_order_modifier
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.streamNode import StreamNode, ExclusiveStreamGroups
from pyMathBitPrecise.bit_utils import mask




@serializeParamsUniq
class AxiS_frameDeparser(AxiSCompBase, TemplateConfigured):
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
                       +-v----------+
        +---------+    |            | output stream
        | field1  +---->  deparser  +--------------->
        +---------+    |            |
                       +-^----------+
        +---------+      |
        | field2  +------+
        +---------+

    .. hwt-autodoc:: _example_AxiS_frameDeparser
    """

    def __init__(self,
                 structT: HdlType,
                 tmpl: Optional[TransTmpl]=None,
                 frames: Optional[List[FrameTmpl]]=None):
        """
        :note: This unit can parse sequence of frames,
            if they are specified by "frames"
        :note: structT can contain fields with variable size like HStream
        """
        self._tmpRegsForSelect = {}
        TemplateConfigured.__init__(self, structT, tmpl, frames)
        AxiSCompBase.__init__(self)

    def _config(self):
        AxiSCompBase._config(self)
        self.USE_STRB = True
        self.T = Param(self._structT)
        self.TRANSACTION_TEMPLATE = Param(self._tmpl)
        self.FRAME_TEMPLATES = Param(None
                                     if self._frames is None
                                     else tuple(self._frames))

    def _mkFieldIntf(self, parent: StructIntf, structField: HStructField):
        """
        Instantiate interface for all members of input type
        """
        t = structField.dtype
        path = parent._field_path / structField.name
        if isinstance(t, HUnion):
            p = UnionSink(t, path, parent._instantiateFieldFn)
            p._fieldsToInterfaces = parent._fieldsToInterfaces
        elif isinstance(t, HStruct):
            p = StructIntf(t, path, parent._instantiateFieldFn)
            p._fieldsToInterfaces = parent._fieldsToInterfaces
        elif isinstance(t, HStream):
            p = AxiStream()
            p._updateParamsFrom(self)
        else:
            p = Handshaked()
            p.DATA_WIDTH = structField.dtype.bit_length()
        return p

    def _declr(self):
        """"
        Parse template and decorate with interfaces
        """
        t = self._structT
        s_t = _get_only_stream(t)
        if s_t is None:
            self.sub_t = [_t for _, _t in separate_streams(t)]
            if len(self.sub_t) == 1:
                # we process all the fields in this component
                self.parseTemplate()
            # else each child will parse it's own part
            # and we join output frames together
        else:
            # only instantiate a component which aligns the stream
            # to correct output format
            self.sub_t = [s_t, ]

        addClkRstn(self)
        with self._paramsShared():
            self.dataOut = self.intfCls()._m()

        if isinstance(self._structT, HStruct):
            intfCls = StructIntf
        elif isinstance(self._structT, HUnion):
            intfCls = UnionSink
        else:
            raise TypeError(self._structT)

        self.dataIn = intfCls(self._structT, tuple(), self._mkFieldIntf)

    def connectPartsOfWord(self, wordData_out: RtlSignal,
                           tPart: Union[TransPart,
                                        ChoicesOfFrameParts],
                           inPorts_out: List[Union[Handshaked,
                                                   StreamNode]],
                           lastInPorts_out: List[Union[Handshaked,
                                                       StreamNode]])\
            ->Tuple[Optional[RtlSignal], Optional[RtlSignal]]:
        """
        Connect transactions parts to signal for word of output stream

        :param wordData_out: signal for word of output stream
        :param tPart: instance of TransPart or ChoicesOfFrameParts to connect
        :param inPorts_out: input interfaces to this transaction part
        :param lastInPorts_out: input interfaces for last parts of transactions
        :return: tuple (strb, keep) if strb/keep driven by input stream, else (None, None)
        """

        tToIntf = self.dataIn._fieldsToInterfaces

        if isinstance(tPart, ChoicesOfFrameParts):
            # connect parts of union to output signal
            high, low = tPart.getBusWordBitRange()
            parentIntf = tToIntf[tPart.origin.parent.getFieldPath()]

            if parentIntf not in self._tmpRegsForSelect.keys():
                sel = HsBuilder(self, parentIntf._select).buff().end
                self._tmpRegsForSelect[parentIntf] = sel

            inPortGroups = ExclusiveStreamGroups()
            lastInPortsGroups = ExclusiveStreamGroups()
            w = tPart.bit_length()

            # tuples (cond, part of data mux for dataOut)
            unionChoices = []
            sk_stashes = []
            # for all choices in union
            for choice in tPart:
                tmp = self._sig("union_tmp_", Bits(w), nop_val=None)
                intfOfChoice = tToIntf[choice.tmpl.getFieldPath()]
                _, _isSelected, isSelectValid = \
                    AxiS_frameParserFieldConnector.choiceIsSelected(self, intfOfChoice)
                unionChoices.append((_isSelected, wordData_out[high:low](tmp)))

                isSelected = _isSelected & isSelectValid

                # build meta for handshake logic sync
                inPortsNode = StreamNode()
                inPortGroups.append((isSelected, inPortsNode))

                lastPortsNode = StreamNode()
                lastInPortsGroups.append((isSelected, lastPortsNode))

                sk_stash = StrbKeepStash()
                # walk all parts in union choice
                start = tPart.startOfPart
                for choicePart in choice:
                    if start != choicePart.startOfPart:
                        # add padding because there is a hole in data
                        _w = choicePart.startOfPart - start
                        assert _w > 0, _w
                        sk_stash.push((_w, 0), (_w, 0))

                    _strb, _keep = self.connectPartsOfWord(
                        tmp, choicePart,
                        inPortsNode.masters,
                        lastPortsNode.masters)
                    sk_stash.push(_strb, _keep)
                    start = choicePart.endOfPart

                if start != tPart.endOfPart:
                    # add padding because there is a hole after
                    _w = tPart.endOfPart - start
                    assert _w > 0, _w
                    sk_stash.push((_w, 0), (_w, 0))

                # store isSelected sig and strb/keep value for later strb/keep resolving
                sk_stashes.append((isSelected, sk_stash))

            # generate data out mux
            SwitchLogic(unionChoices,
                        default=wordData_out(None))

            inPorts_out.append(inPortGroups)
            lastInPorts_out.append(lastInPortsGroups)
            # resolve strb/keep from strb/keep and isSelected of union members
            if w % 8 != 0:
                raise NotImplementedError(w)
            strb, keep = reduce_conditional_StrbKeepStashes(sk_stashes)
        else:
            # connect parts of fields to output signal
            high, low = tPart.getBusWordBitRange()
            if tPart.isPadding:
                wordData_out[high:low](None)
            else:
                intf = tToIntf[tPart.tmpl.getFieldPath()]
                fhigh, flow = tPart.getFieldBitRange()
                wordData_out[high:low](
                    self.byteOrderCare(intf.data)[fhigh:flow])
                inPorts_out.append(intf)

                if tPart.isLastPart():
                    lastInPorts_out.append(intf)

            w = tPart.bit_length()
            strb = int(not tPart.isPadding)
            keep = int(not tPart.canBeRemoved)
        return ((w, strb), (w, keep))

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

    def delegate_to_children(self):
        """
        For the cases where output frames contains the streams which does
        not have start aligned to a frame word boundary, we have to build
        rest of the frame in child FrameForge and then instantiate
        AxiS_FrameJoin which will join such a unaligned frames together.
        """
        Cls = self.__class__
        assert len(self.sub_t) > 1, "We need to delegate to children only " \
            "if there is something which we can't do in this comp. directly"
        children = HObjList()
        for t in self.sub_t:
            _t = _get_only_stream(t)
            if _t is None:
                # we need a child to build a sub frame
                c = Cls(t)
                c.USE_KEEP = self.USE_STRB | self.DATA_WIDTH != 8
            else:
                # we will connect stream directly
                c = None

            children.append(c)

        with self._paramsShared(
                exclude=({"USE_KEEP", "USE_STRB",
                          "T", "TRANSACTION_TEMPLATE", "FRAME_TEMPLATES"}, {})):
            self.children = children

        fjoin = AxiS_FrameJoin()
        sub_t_flatten = [to_primitive_stream_t(s_t) for s_t in self.sub_t]
        fjoin.T = HStruct(
            *((s_t, f"frame{i:d}")
              for i, s_t in enumerate(sub_t_flatten))
        )
        fjoin._updateParamsFrom(
            self, exclude=({"USE_KEEP", "T"}, {}))
        # has to have keep, because we know that atleast one output will
        # have unaligned start
        fjoin.USE_KEEP = True
        self.frame_join = fjoin

        dout = self.dataOut
        if not self.USE_KEEP:
            exclude = (fjoin.dataOut.keep,)
        else:
            exclude = ()

        dout(fjoin.dataOut, exclude=exclude)

        propagateClkRstn(self)
        for i, c in enumerate(children):
            if c is None:
                # find the input stream
                _t, child_out = drill_down_in_HStruct_fields(
                    self.sub_t[i], self.dataIn)
                assert isinstance(_t, HStream)
            else:
                # connect children inputs
                connect_optional_with_best_effort_axis_mask_propagation(
                    self.dataIn, c.dataIn)
                child_out = c.dataOut

            # join children output streams to output
            fj_in = fjoin.dataIn[i]
            if fj_in.USE_KEEP and not child_out.USE_KEEP:
                if child_out.USE_STRB:
                    exclude = {child_out.strb, fj_in.keep}
                    fj_in.keep(child_out.strb)
                    if fj_in.USE_STRB:
                        fj_in.strb(child_out.strb)
                else:
                    exclude = {fj_in.keep}
                    keep_all = mask(fj_in.keep._dtype.bit_length())
                    fj_in.keep(keep_all)
                    if fj_in.USE_STRB:
                        fj_in.strb(keep_all)
            elif not self.USE_STRB and child_out.USE_STRB:
                exclude = (child_out.strb,)
            else:
                exclude = ()

            fj_in(child_out, exclude=exclude)

    def _create_frame_build_logic(self):
        self.byteOrderCare = get_byte_order_modifier(self.dataOut)

        STRB_ALL = mask(int(self.DATA_WIDTH // 8))
        words = list(self.chainFrameWords())
        dout = self.dataOut
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
        extra_keeps = []
        for i, transParts, isLast in words:
            inversedIndx = maxWordIndex - i

            # input ports for value of this output word
            inPorts = []
            # input ports which value should be consumed on this word
            lastInPorts = []
            if multipleWords:
                wordData = self._sig(f"word{i:d}", dout.data._dtype)
            else:
                wordData = self.dataOut.data

            sk_stash = StrbKeepStash()
            for tPart in transParts:
                strb, keep = self.connectPartsOfWord(
                    wordData, tPart,
                    inPorts,
                    lastInPorts)
                sk_stash.push(strb, keep)
            sk_stash.pop(inversedIndx, extra_strbs, extra_keeps, STRB_ALL)

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
            default = [wordCntr_inversed(maxWordIndex), ]
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

        if multipleWords:
            if self.USE_STRB:
                strb = dout.strb
                Switch(wordCntr_inversed).add_cases([
                    (i, strb(v)) for i, v in extra_strbs
                ]).Default(
                    strb(STRB_ALL)
                )
            if self.USE_KEEP:
                keep = dout.keep
                Switch(wordCntr_inversed).add_cases([
                    (i, keep(v)) for i, v in extra_keeps
                ]).Default(
                    keep(STRB_ALL)
                )
        else:
            if extra_strbs:
                m = extra_strbs[0][1]
            else:
                m = STRB_ALL
            if self.USE_STRB:
                dout.strb(m)

            if extra_keeps:
                m = extra_keeps[0][1]
            else:
                m = STRB_ALL

            if self.USE_KEEP:
                dout.keep(m)

    def _impl(self):
        """
        Iterate over words in template and create stream output mux and fsm.
        Frame specifier can contains unions/streams/padding/unaligned items
        and other features which makes code below complex.
        Frame specifier can also describe multiple frames.
        """
        if len(self.sub_t) > 1:
            self.delegate_to_children()
        else:
            s_t = _get_only_stream(self._structT)
            if s_t is None:
                self._create_frame_build_logic()
            else:
                if not isinstance(s_t.element_t, Bits):
                    raise NotImplementedError(s_t)
                # no special care required because the stream
                # is already in correct format
                din = self.dataIn
                while not isinstance(din, AxiStream):
                    # dril down in HdlType to find a stream
                    assert len(din._interfaces) == 1
                    din = din._interfaces[0]
                self.dataOut(din)


def _example_AxiS_frameDeparser():
    from hwtLib.types.ctypes import uint64_t, uint8_t, uint16_t, uint32_t

    # t = HStruct(
    #    (uint64_t, "item0"),
    #    (uint64_t, None),  # name = None means field is padding
    #    (uint64_t, "item1"),
    #    (uint8_t, "item2"), (uint8_t, "item3"), (uint16_t, "item4")
    # )
    # t = HUnion(
    #     (HStruct(
    #         (uint64_t, "itemA0"),
    #         (uint64_t, "itemA1")
    #         ), "frameA"),
    #     (HStruct(
    #         (uint32_t, "itemB0"),
    #         (uint32_t, "itemB1"),
    #         (uint32_t, "itemB2"),
    #         (uint32_t, "itemB3")
    #         ), "frameB")
    # )
    t = HUnion(
        (HStruct((uint8_t, "data"), (uint8_t, None)), "u0"),
        (HStruct((uint8_t, None), (uint8_t, "data")), "u1"),
    )

    u = AxiS_frameDeparser(t)
    u.DATA_WIDTH = 16
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_AxiS_frameDeparser()
    print(to_rtl_str(u))
    # print(u._frames)
