#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat, SwitchLogic
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIODataRdVld, HwIOSignal
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil, isPow2
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.amba.axis_comp.builder import Axi4SBuilder
from hwtLib.amba.axis_comp.fifo import Axi4SFifo
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode
from pyMathBitPrecise.bit_utils import mask


class Axi4S_fifoMeasuring(HwModule):
    """
    Fifo which are counting sizes of frames and sends it over
    dedicated handshaked interface "sizes"

    .. hwt-autodoc:: _example_Axi4S_fifoMeasuring
    """

    def _config(self):
        Axi4Stream._config(self)
        self.SIZES_BUFF_DEPTH = HwParam(16)
        self.MAX_LEN = HwParam((2048 // 8) - 1)
        self.EXPORT_ALIGNMENT_ERROR = HwParam(False)

    def getAlignBitsCnt(self):
        return log2ceil(self.DATA_WIDTH // 8)

    def _declr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = Axi4Stream()
            self.dataOut = Axi4Stream()._m()
            db = self.dataBuff = Axi4SFifo()
            # to place fifo in bram
            db.DEPTH = (self.MAX_LEN + 1) * 2

        self.sizes = HwIODataRdVld()._m()
        self.sizes.DATA_WIDTH = (log2ceil(self.MAX_LEN)
                                 +1
                                 +self.getAlignBitsCnt())

        sb = self.sizesBuff = HandshakedFifo(HwIODataRdVld)
        sb.DEPTH = self.SIZES_BUFF_DEPTH
        sb.DATA_WIDTH = self.sizes.DATA_WIDTH

        if self.EXPORT_ALIGNMENT_ERROR:
            assert self.USE_STRB, "Error can not happend"\
                " when there is no validity mask for alignment"
            self.errorAlignment = HwIOSignal()._m()

        assert isPow2(self.DATA_WIDTH)

    def _impl(self):
        propagateClkRstn(self)
        dIn = Axi4SBuilder(self, self.dataIn).buff().end

        sb = self.sizesBuff
        db = self.dataBuff

        wordCntr = self._reg("wordCntr",
                             HBits(log2ceil(self.MAX_LEN) + 1),
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
            rem = self._sig("rem", HBits(log2ceil(BYTE_CNT)))

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
            rem = HBits(log2ceil(BYTE_CNT)).from_py(0)

        sb.dataIn.data(Concat(length, rem))

        db.dataIn(dIn, exclude=[dIn.valid, dIn.ready, dIn.last])
        db.dataIn.last(last)

        StreamNode(masters=[dIn],
                   slaves=[sb.dataIn, db.dataIn],
                   extraConds={sb.dataIn: last
                               }).sync()

        self.sizes(sb.dataOut)
        self.dataOut(db.dataOut)


def _example_Axi4S_fifoMeasuring():
    m = Axi4S_fifoMeasuring()
    m.USE_STRB = True
    # u.EXPORT_ALIGNMENT_ERROR = True
    m.MAX_LEN = 15
    m.SIZES_BUFF_DEPTH = 4
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_Axi4S_fifoMeasuring()
    print(to_rtl_str(m))
