#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Optional, Union, Dict

from hwt.code import log2ceil, Switch, If, isPow2, SwitchLogic, connect
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
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.byteOrder import reverseByteOrder
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.frameParser import AxiS_frameParser
from hwtLib.abstract.template_configured import TemplateConfigured,\
    separate_footers, to_primitive_stream_t
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.streamNode import StreamNode, ExclusiveStreamGroups
from pyMathBitPrecise.bit_utils import mask
from hwtLib.amba.axis_comp.frame_join import AxiS_FrameJoin
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.interface import Interface
from ipCorePackager.constants import DIRECTION


def _get_only_stream(t: HdlType):
    """
    Return HStream if base datatype is HStream.
    (HStream field may be nested in HStruct)
    """
    if isinstance(t, HStream):
        return t
    elif isinstance(t, HStruct) and len(t.fields) == 1:
        return _get_only_stream(t.fields[0].dtype)
    return None


def _connect_if_present_on_dst(src: Interface, dst: Interface, dir_reverse=False, connect_keep_to_strb=False):
    if not src._interfaces:
        assert not dst._interfaces, (src, dst)
        if dir_reverse:
            src(dst)
        else:
            dst(src)
    for _s in src._interfaces:
        _d = getattr(dst, _s._name, None)
        if _d is None:
            continue
        if _d._masterDir == DIRECTION.IN:
            rev = not dir_reverse
        else:
            rev = dir_reverse

        _connect_if_present_on_dst(_s, _d, dir_reverse=rev,
                                   connect_keep_to_strb=connect_keep_to_strb)
        if _s._name == "strb" and connect_keep_to_strb:
            _connect_if_present_on_dst(_s, dst.keep, dir_reverse=rev,
                                       connect_keep_to_strb=connect_keep_to_strb)



class AxiS_frameForge(AxiSCompBase, TemplateConfigured):
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
        self.OUT_OFFSET = Param(0)

    def _mkFieldIntf(self, parent: StructIntf, structField: HStructField):
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
            p._updateParamsFrom(self)
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
        t = self._structT
        s_t = _get_only_stream(t)
        if s_t is None:
            self.sub_t = [_t for _, _t in separate_footers(t, {})]
            if len(self.sub_t) == 1:
                self.parseTemplate()
                # else each child will parse it's own part
        else:
            # only instanciate a compoment which aligns the sream
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

    def _delegate_to_children(self):
        Cls = self.__class__
        assert len(self.sub_t) > 1, "We need to delegate to children only " \
            "if there is something which we can do in this comp. directly"
        children = HObjList([Cls(t) for t in self.sub_t])
        for c in children:
            c.USE_KEEP = True

        with self._paramsShared(exclude=({"USE_KEEP"}, {})):
            self.children = children

        frame_join = AxiS_FrameJoin()
        sub_t_flatten = [to_primitive_stream_t(s_t) for s_t in self.sub_t]
        frame_join.T = HStruct(
            *((s_t, "frame%d" % i)
              for i, s_t in enumerate(sub_t_flatten))
        )
        frame_join._updateParamsFrom(self, exclude=({"USE_KEEP", }, {}))
        self.frame_join = frame_join
        connect(frame_join.dataOut, self.dataOut, exclude=frame_join.dataOut.keep)

        propagateClkRstn(self)
        for i, c in enumerate(children):
            # connect children inputs
            _connect_if_present_on_dst(self.dataIn, c.dataIn, connect_keep_to_strb=True)
            # join children output streams to output
            frame_join.dataIn[i](c.dataOut)

    def _create_frame_build_logic(self):
        if self.OUT_OFFSET != 0:
            raise NotImplementedError()

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
            if self.USE_KEEP:
                if not extra_strbs:
                    dout.keep(STRB_ALL)
                else:
                    raise NotImplementedError()
        else:
            if extra_strbs:
                m = extra_strbs[0][1]
            else:
                m = STRB_ALL
            strb(m)
            if self.USE_KEEP:
                # [fixme] derive keep from size of data, rather than strb, because
                # there may be some padding in original type
                dout.keep(m)

    def _impl(self):
        """
        Iterate over words in template and create stream output mux and fsm.
        Frame specifier can contains unions/streams/padding/unaligned items
        and other features which makes code below complex.
        Frame specifier can also describe multiple frames.
        """
        if len(self.sub_t) > 1:
            self._delegate_to_children()
            return
        else:
            s_t = _get_only_stream(self._structT)
            if s_t is not None:
                if not isinstance(s_t.element_t, Bits):
                    raise NotImplementedError(s_t)
                if s_t.start_offsets == [self.OUT_OFFSET]:
                    # no special care required because the stream
                    # is already in correct format
                    din = self.dataIn
                    while not isinstance(din, AxiStream):
                        # dril down in HdlType to find a stream
                        assert len(din._interfaces) == 1
                        din = din._interfaces[0]
                    self.dataOut(din)
                else:
                    raise NotImplementedError("delegate to AxiS_FrameJoin")
                return

        self._create_frame_build_logic()


def _example_AxiS_frameForge():
    from hwtLib.types.ctypes import uint64_t, uint8_t, uint16_t

    t = HStruct(
        (uint64_t, "item0"),
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
