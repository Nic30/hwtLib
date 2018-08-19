#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, log2ceil
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Handshaked, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.mem.ram import RamSingleClock
from hwt.synthesizer.hObjList import HObjList


def splitOnBytes(sig):
    return [sig[(i + 1) * 8:i * 8]
            for i in range(sig._dtype.bit_length() // 8)]


class ByteCntrsRes(Handshaked):

    def _declr(self):
        Handshaked._declr(self)
        self.last = Signal()


class ByteCntrs(Unit):
    """
    Count the appereance of bytes in input frame
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.MAX_FRAME_LEN = Param(1530)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = AxiStream()

        DW = int(self.DATA_WIDTH)
        assert DW % 8 == 0, "Has to be byte aligned"
        self.CNTR_WIDTH = log2ceil(self.MAX_FRAME_LEN // self.DATA_WIDTH // 8)
        self.res = ByteCntrsRes()._m()
        self.res.DATA_WIDTH.set(self.CNTR_WIDTH)

        # for each byte in data word there is separate table to make
        # counting faster
        self.counters = HObjList(
            RamSingleClock() for _ in range(DW // 8)
        )
        
        for c in self.counters:
            c.PORT_CNT.set(2)
            c.DATA_WIDTH.set(self.CNTR_WIDTH)
            c.ADDR_WIDTH.set(8)

    def _impl(self):
        propagateClkRstn(self)
        DW = int(self.DATA_WIDTH)
        B_CNT = DW // 8
        din = self.dataIn
        # do cleanup of counters logic
        doCleanup = self._reg("do_cleanup", defVal=1)
        cleanupAddr = self._reg("do_cleanup", Bits(8), defVal=0)
        If(doCleanup,
            If(cleanupAddr._eq(255),
               doCleanup(0)
            )
        )

        # counter incrementing logic
        inReady = self._sig("in_ready")
        prev = self._reg("prev", din.data._dtype)
        prevStrb = self._reg("prev_strb", din.strb._dtype, 0)
        dinBytes = splitOnBytes(din.data)
        prevDinBytes = splitOnBytes(prev)

        prev(din.data)

        for bi in range(B_CNT):
            _in = dinBytes[bi]
            _prevIn = prevDinBytes[bi]
            c = self.counters[bi]
            # from first port of ram where the counters are is continuesly readed from addres of in byte
            c.a.addr(_in)
            c.a.en(1)
            c.a.we(0)
            c.a.din(None)

            If(prevStrb[bi] & _prevIn._eq(_in),
               # check if previous byte was same and we have to add it to currently loading value
               prevStrb.next[bi](0),
               c.b.din(c.a.dout + 2)
            ).Else(
               # previous value was something different and we need to load counter from ram first
               prevStrb.next[bi](din.valid & inReady & din.strb[bi]),
               c.b.din(c.a.dout + 1)
            )

            c.b.addr(_prevIn)
            c.b.en(prevStrb[bi])
            c.b.we(1)


class EntropyDetector(Unit):
    """
    Detect the entropy of the frame/packet

    Appereance of bytes is counted and at the end the entropy is resolved from this counters


    :ivar DATA_WIDTH: data width of input interface
    :ivar ENTROPY_WIDTH: data width of entropy output
    :ivar MAX_FRAME_LEN: frame len which is used to resolve widths of byte appereance conters
    """

    def _config(self):
        ByteCntrs._config(self)
        self.ENTROPY_WIDTH = Param(16)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = AxiStream()

        self.entropy = Handshaked()
        self.entropy._replaceParam("DATA_WIDTH", self.ENTROPY_WIDTH)
        self.byteCntrs = ByteCntrs()

    def _impl(self):
        # log2 http://www.ijsps.com/uploadfile/2014/1210/20141210051242629.pdf
        propagateClkRstn(self)
        self.byteCntrs.dataIn(self.dataIn)

        # todo accululate result from self.byteCntrs.res


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = ByteCntrs()
    print(toRtl(u))
