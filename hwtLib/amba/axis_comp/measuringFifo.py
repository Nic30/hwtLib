#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.bitmask import mask
from hwt.code import If, connect, Concat, log2ceil, SwitchLogic
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Handshaked, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.amba.axis_comp.fifo import AxiSFifo
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.mem.fifo import Fifo


class AxiS_measuringFifo(Unit):
    """
    Fifo which are counting sizes of frames and sends it over
    dedicated handshaked interface "sizes"
    """
    def __init__(self, stream_t=AxiStream):
        self._stream_t = stream_t
        super(AxiS_measuringFifo, self).__init__()

    def _config(self):
        Fifo._config(self)
        self.SIZES_BUFF_DEPTH = Param(16)
        self.MAX_LEN = Param((2048 // 8) - 1)
        self.EXPORT_ALIGNMENT_ERROR = Param(False)

    def getAlignBitsCnt(self):
        return log2ceil(self.DATA_WIDTH // 8).val

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = self._stream_t()
            self.dataOut = self._stream_t()._m()

        self.sizes = Handshaked()._m()
        self.sizes.DATA_WIDTH.set(log2ceil(self.MAX_LEN)
                                  + 1
                                  + self.getAlignBitsCnt())

        db = self.dataBuff = AxiSFifo(self._stream_t)
        # to place fifo in bram
        db.DATA_WIDTH.set(self.DATA_WIDTH)
        db.DEPTH.set((self.MAX_LEN + 1) * 2)

        sb = self.sizesBuff = HandshakedFifo(Handshaked)
        sb.DEPTH.set(self.SIZES_BUFF_DEPTH)
        sb.DATA_WIDTH.set(self.sizes.DATA_WIDTH.get())

        if self.EXPORT_ALIGNMENT_ERROR:
            self.errorAlignment = Signal()._m()

    def _impl(self):
        propagateClkRstn(self)
        dIn = AxiSBuilder(self, self.dataIn).buff().end
        STRB_BITS = dIn.strb._dtype.bit_length()

        sb = self.sizesBuff
        db = self.dataBuff

        wordCntr = self._reg("wordCntr",
                             Bits(log2ceil(self.MAX_LEN) + 1),
                             defVal=0)

        overflow = wordCntr._eq(self.MAX_LEN)
        last = dIn.last | overflow
        If(StreamNode(masters=[dIn], slaves=[sb.dataIn, db.dataIn]).ack(),
            If(last,
                wordCntr(0)
            ).Else(
                wordCntr(wordCntr + 1)
            )
        )
        rem = self._sig("rem", Bits(log2ceil(STRB_BITS)))
        SwitchLogic(
            cases=[
                (dIn.strb[i], rem(0 if i == STRB_BITS - 1 else i + 1))
                for i in reversed(range(STRB_BITS))],
            default=[
                rem(0),

            ]
        )
        if self.EXPORT_ALIGNMENT_ERROR:
            errorAlignment = self._reg("errorAlignment_reg", defVal=0)
            self.errorAlignment(errorAlignment)
            If(dIn.valid & (dIn.strb != mask(STRB_BITS)) & ~dIn.last,
               errorAlignment(1)
               )

        length = self._sig("length", wordCntr._dtype)
        If(last & (dIn.strb != mask(STRB_BITS)),
            length(wordCntr)
        ).Else(
            length(wordCntr + 1)
        )

        sb.dataIn.data(Concat(length, rem))

        connect(dIn, db.dataIn, exclude=[dIn.valid, dIn.ready, dIn.last])
        db.dataIn.last(last)

        StreamNode(masters=[dIn],
                   slaves=[sb.dataIn, db.dataIn],
                   extraConds={sb.dataIn: last
                               }).sync()

        self.sizes(sb.dataOut)
        connect(db.dataOut, self.dataOut)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = AxiS_measuringFifo()
    #u.EXPORT_ALIGNMENT_ERROR.set(True)
    u.MAX_LEN.set(15)
    u.SIZES_BUFF_DEPTH.set(4)
    print(toRtl(u))
