#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from hwt.code import StaticForEach
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Handshaked, Signal
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.template_configured import TemplateConfigured
from hwtLib.amba.axis_comp.frame_parser import AxiS_frameParser
from hwtLib.amba.datapump.intf import AxiRDatapumpIntf, AddrSizeHs
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.streamNode import StreamNode


class StructReader(AxiS_frameParser):
    """
    This unit downloads required structure fields over rDatapump
    interface from address specified by get interface

    :ivar ~.ID: Param, id for transactions on bus
    :ivar ~.READ_ACK: Param, if true ready on "get" will be set only
        when component is in idle (if false "get"
        is regular handshaked interface)
    :ivar ~.SHARED_READY: Param, if this is true field interfaces
        will be of type VldSynced and single ready signal
        will be used for all else every interface
        will be instance of Handshaked and it
        will have it's own ready(rd) signal
    :attention: interfaces of field will not send data in same time

    .. aafig::

            get (base addr)          +---------+
         +----------------   +------>| field0  |
                         |   |       +---------+
                         v   |
            bus req   +------+--+
         <------------+         |    +---------+
                      | reader  +--->| field1  |
         +----------->|         |    +---------+
            bus data  +-------+-+
                              |      +---------+
                              +----->| field2  |
                                     +---------+

    :note: names in the picture are just illustrative

    .. hwt-autodoc:: _example_StructReader
    """

    def __init__(self, structT, tmpl=None, frames=None):
        """
        :param structT: instance of HStruct which specifies data format to download
        :param tmpl: instance of TransTmpl for this structT
        :param frames: list of FrameTmpl instances for this tmpl
        :note: if tmpl and frames are None they are resolved from structT parseTemplate
        :note: this unit can parse sequence of frames, if they are specified by "frames"
        :attention: interfaces for each field in struct will be dynamically created
        :attention: structT can not contain fields with variable size like HStream
        """
        Unit.__init__(self)
        assert isinstance(structT, HStruct)
        TemplateConfigured.__init__(self, structT, tmpl=tmpl, frames=frames)

    def _config(self):
        self.ID = Param(0)
        AxiRDatapumpIntf._config(self)
        self.USE_STRB = False
        self.READ_ACK = Param(False)
        self.SHARED_READY = Param(False)

    def maxWordIndex(self):
        return max(f.endBitAddr - 1 for f in self._frames) // self.DATA_WIDTH

    def maxBytesInTransaction(self):
        return ceil(max(
                    [f.parts[-1].endOfPart - f.startBitAddr for f in self._frames]
                    ) / 8)

    def parseTemplate(self):
        if self._tmpl is None:
            self._tmpl = TransTmpl(self._structT)
        if self._frames is None:
            DW = self.DATA_WIDTH
            frames = FrameTmpl.framesFromTransTmpl(
                        self._tmpl,
                        DW,
                        trimPaddingWordsOnStart=True,
                        trimPaddingWordsOnEnd=True)

            self._frames = list(frames)

    def _declr(self):
        addClkRstn(self)
        self.dataOut = StructIntf(self._structT,
                                  tuple(),
                                  self._mkFieldIntf)._m()

        g = self.get = Handshaked()  # data signal is addr of structure to download
        g.DATA_WIDTH = self.ADDR_WIDTH
        self.parseTemplate()

        with self._paramsShared():
            # interface for communication with datapump
            self.rDatapump = AxiRDatapumpIntf()._m()
            self.rDatapump.MAX_BYTES = self.maxBytesInTransaction()

        with self._paramsShared(exclude=({"ID_WIDTH"}, set())):
            self.parser = AxiS_frameParser(self._structT,
                                           tmpl=self._tmpl,
                                           frames=self._frames)
            self.parser.SYNCHRONIZE_BY_LAST = False

        if self.SHARED_READY:
            self.ready = Signal()

    def driveReqRem(self, req: AddrSizeHs, MAX_BITS: int):
        return req.rem(ceil((MAX_BITS % self.DATA_WIDTH) / 8))

    def _impl(self):
        propagateClkRstn(self)
        req = self.rDatapump.req

        if self.READ_ACK:
            get = self.get
        else:
            get = HsBuilder(self, self.get).buff().end

        def propagateRequest(frame, indx):
            isLastFrame = indx == len(self._frames) - 1
            s = [
                req.addr(get.data + frame.startBitAddr // 8),
                req.len(frame.getWordCnt() - 1),
                self.driveReqRem(req, frame.parts[-1].endOfPart - frame.startBitAddr),
                req.vld(get.vld),
                get.rd(req.rd if isLastFrame else 0)
            ]

            ack = StreamNode(masters=[get], slaves=[self.rDatapump.req]).ack()
            return s, ack

        StaticForEach(self, self._frames, propagateRequest)

        r = self.rDatapump.r
        data_sig_to_exclude = []
        if self.ID_WIDTH:
            req.id(self.ID)
        if hasattr(r, "id"):
            data_sig_to_exclude.append(r.id)
        if hasattr(r, "strb"):
            data_sig_to_exclude.append(r.strb)

        self.parser.dataIn(r, exclude=data_sig_to_exclude)

        for _, field in self._tmpl.walkFlatten():
            p = field.getFieldPath()
            myIntf = self.dataOut._fieldsToInterfaces[p]
            parserIntf = self.parser.dataOut._fieldsToInterfaces[p]
            myIntf(parserIntf)


def _example_StructReader():
    from hwtLib.types.ctypes import uint16_t, uint32_t, uint64_t

    s = HStruct(
        (uint64_t, "item0"),  # tuples (type, name) where type has to be instance of Bits type
        (uint64_t, None),  # name = None means this field will be ignored
        (uint64_t, "item1"),
        (uint64_t, None),
        (uint16_t, "item2"),
        (uint16_t, "item3"),
        (uint32_t, "item4"),

        (uint32_t, None),
        (uint64_t, "item5"),  # this word is split on two bus words
        (uint32_t, None),

        (uint64_t, None),
        (uint64_t, None),
        (uint64_t, None),
        (uint64_t, "item6"),
        (uint64_t, "item7"),
        )

    u = StructReader(s)
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_StructReader()
    print(to_rtl_str(u))
