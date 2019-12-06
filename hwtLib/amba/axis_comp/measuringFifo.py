#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, connect, Concat, log2ceil, SwitchLogic, isPow2
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Handshaked, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit

from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.amba.axis_comp.fifo import AxiSFifo
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode
from hwt.hdl.typeShortcuts import vec
from pyMathBitPrecise.bit_utils import mask


class AxiS_measuringFifo(Unit):
    """
    Fifo which are counting sizes of frames and sends it over
    dedicated handshaked interface "sizes"

    .. hwt-schematic:: _example_AxiS_measuringFifo
    """

    def _config(self):
        AxiStream._config(self)
        self.SIZES_BUFF_DEPTH = Param(16)
        self.MAX_LEN = Param((2048 // 8) - 1)
        self.EXPORT_ALIGNMENT_ERROR = Param(False)

    def getAlignBitsCnt(self):
        return log2ceil(self.DATA_WIDTH // 8)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = AxiStream()
            self.dataOut = AxiStream()._m()
            db = self.dataBuff = AxiSFifo()
            # to place fifo in bram
            db.DEPTH = (self.MAX_LEN + 1) * 2

        self.sizes = Handshaked()._m()
        self.sizes.DATA_WIDTH = (log2ceil(self.MAX_LEN)
                                 + 1
                                 + self.getAlignBitsCnt())

        sb = self.sizesBuff = HandshakedFifo(Handshaked)
        sb.DEPTH = self.SIZES_BUFF_DEPTH
        sb.DATA_WIDTH = self.sizes.DATA_WIDTH

        if self.EXPORT_ALIGNMENT_ERROR:
            assert self.USE_STRB, "Error can not happend"\
                " when there is no validity mask for alignment"
            self.errorAlignment = Signal()._m()

        assert isPow2(self.DATA_WIDTH)

    def _impl(self):
        propagateClkRstn(self)
        dIn = AxiSBuilder(self, self.dataIn).buff().end

        sb = self.sizesBuff
        db = self.dataBuff

        wordCntr = self._reg("wordCntr",
                             Bits(log2ceil(self.MAX_LEN) + 1),
                             def_val=0)

        overflow = wordCntr._eq(self.MAX_LEN)
        last = dIn.last | overflow
        If(StreamNode(masters=[dIn], slaves=[sb.dataIn, db.dataIn]).ack(),
            If(last,
                wordCntr(0)
            ).Else(
                wordCntr(wordCntr + 1)
            )
        )

        length = self._sig("length", wordCntr._dtype)
        BYTE_CNT = dIn.data._dtype.bit_length() // 8
        if dIn.USE_STRB:
            # compress strb mask as binary number
            rem = self._sig("rem", Bits(log2ceil(BYTE_CNT)))

            SwitchLogic(
                cases=[
                    (dIn.strb[i], rem(0 if i == BYTE_CNT - 1 else i + 1))
                    for i in reversed(range(BYTE_CNT))],
                default=[
                    rem(0),
                ]
            )
            if self.EXPORT_ALIGNMENT_ERROR:
                errorAlignment = self._reg("errorAlignment_reg", def_val=0)
                self.errorAlignment(errorAlignment)
                If(dIn.valid & (dIn.strb != mask(BYTE_CNT)) & ~dIn.last,
                   errorAlignment(1)
                )

            If(last & (dIn.strb != mask(BYTE_CNT)),
                length(wordCntr)
            ).Else(
                length(wordCntr + 1)
            )
        else:
            length(wordCntr + 1)
            rem = vec(0, log2ceil(BYTE_CNT))

        sb.dataIn.data(Concat(length, rem))

        connect(dIn, db.dataIn, exclude=[dIn.valid, dIn.ready, dIn.last])
        db.dataIn.last(last)

        StreamNode(masters=[dIn],
                   slaves=[sb.dataIn, db.dataIn],
                   extraConds={sb.dataIn: last
                               }).sync()

        self.sizes(sb.dataOut)
        connect(db.dataOut, self.dataOut)


def _example_AxiS_measuringFifo():
    u = AxiS_measuringFifo()
    u.USE_STRB = True
    # u.EXPORT_ALIGNMENT_ERROR = True
    u.MAX_LEN = 15
    u.SIZES_BUFF_DEPTH = 4
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiS_measuringFifo()
    print(toRtl(u))
