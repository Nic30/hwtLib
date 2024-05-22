#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Tuple, Union

from hwt.code import If
from hwt.hwIOs.std import HwIOVectSignal, HwIOClk, HwIORst_n, HwIORst
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interfaceLevel.utils import HwIO_pack, \
    HwIO_connectPacked
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.mem.fifo import Fifo


@serializeParamsUniq
class HandshakedFifo(HandshakedCompBase):
    """
    Synchronous FIFO for handshaked interfaces

    .. figure:: ./_static/HandshakedFifo.png

    .. hwt-autodoc:: _example_HandshakedFifo
    """
    FIFO_CLS = Fifo
    NON_DATA_BITS_CNT = 2  # 2 for control (valid, ready)

    @override
    def hwConfig(self):
        self.DEPTH:int = HwParam(0)
        self.EXPORT_SIZE: bool = HwParam(False)
        self.EXPORT_SPACE: bool = HwParam(False)
        self.INIT_DATA: tuple = HwParam(())
        super().hwConfig()

    def _declr_io(self):
        addClkRstn(self)

        with self._hwParamsShared():
            self.dataIn = self.hwIOCls()
            self.dataOut = self.hwIOCls()._m()

        SIZE_W = log2ceil(self.DEPTH + 1 + 1)
        if self.EXPORT_SIZE:
            self.size:HwIOVectSignal = HwIOVectSignal(SIZE_W, signed=False)._m()
        if self.EXPORT_SPACE:
            self.space:HwIOVectSignal = HwIOVectSignal(SIZE_W, signed=False)._m()

    @override
    def hwDeclr(self):
        assert self.DEPTH > 0, \
            "Fifo is disabled in this case, do not use it entirely"
        assert self.DEPTH > 1 , \
            "Fifo is too small, fifo pointers would not work correctly, use register(s) instead"
        assert len(self.INIT_DATA) <= len(self.INIT_DATA)
        self._declr_io()

        f = self.fifo = self.FIFO_CLS()
        DW = self.dataIn._bit_length() - self.NON_DATA_BITS_CNT
        f.DATA_WIDTH = DW
        f.DEPTH = self.DEPTH - 1  # because there is an extra register
        if len(self.INIT_DATA) == self.DEPTH:
            f.INIT_DATA_FIRST_WORD = self.INIT_DATA[0]
            f.INIT_DATA = self.INIT_DATA[1:]
        else:
            f.INIT_DATA = self.INIT_DATA

        f.EXPORT_SIZE = self.EXPORT_SIZE
        f.EXPORT_SPACE = self.EXPORT_SPACE

    def _connect_size_and_space(self, out_vld, fifo):
        if self.EXPORT_SIZE:
            size_tmp = self._sig("size_tmp", self.size._dtype)
            size_tmp(fifo.size, fit=True)

            If(out_vld,
               self.size(size_tmp + 1)
            ).Else(
               self.size(size_tmp)
            )

        if self.EXPORT_SPACE:
            space_tmp = self._sig("space_tmp", self.size._dtype)
            space_tmp(fifo.space, fit=True)

            If(out_vld,
               self.space(space_tmp)
            ).Else(
               self.space(space_tmp + 1)
            )

    def _connect_fifo_in(self):
        rd = self.get_ready_signal
        vld = self.get_valid_signal

        din = self.dataIn
        fIn = self.fifo.dataIn
        wr_en = ~fIn.wait
        rd(din)(wr_en)
        if fIn.DATA_WIDTH > 0:
            fIn.data(HwIO_pack(din, exclude=[vld(din), rd(din)]))
        fIn.en(vld(din) & wr_en)

    def _connect_fifo_out(self, out_clk, out_rst):
        rd = self.get_ready_signal
        vld = self.get_valid_signal

        fOut = self.fifo.dataOut
        dout = self.dataOut
        out_vld = self._reg("out_vld", def_val=int(len(self.INIT_DATA) == self.DEPTH), clk=out_clk, rst=out_rst)
        vld(dout)(out_vld)

        if fOut.DATA_WIDTH > 0:
            HwIO_connectPacked(fOut.data,
                          dout,
                          exclude=[vld(dout), rd(dout)])
        fOut.en((rd(dout) | ~out_vld) & ~fOut.wait)
        If(rd(dout) | ~out_vld,
           out_vld(~fOut.wait)
        )
        return out_vld

    @override
    def hwImpl(self,
              clk_rst: Optional[Tuple[
                  Tuple[HwIOClk, Union[HwIORst, HwIORst_n]],
                  Tuple[HwIOClk, Union[HwIORst, HwIORst_n]]]]=None):
        """
        :param clk_rst: optional tuple ((inClk, inRst), (outClk, outRst))
        """
        # connect clock and resets
        if clk_rst is None:
            propagateClkRstn(self)
            out_clk = None
            out_rst = None
        else:
            (in_clk, in_rst), (out_clk, out_rst) = clk_rst
            f = self.fifo
            f.dataIn_clk(in_clk)
            f.dataIn_rst_n(in_rst)
            f.dataOut_clk(out_clk)
            f.dataOut_rst_n(out_rst)

        self._connect_fifo_in()
        out_vld = self._connect_fifo_out(out_clk, out_rst)
        self._connect_size_and_space(out_vld, self.fifo)


def _example_HandshakedFifo():
    from hwt.hwIOs.std import HwIODataRdVld
    m = HandshakedFifo(HwIODataRdVld)
    m.DEPTH = 8
    m.DATA_WIDTH = 4
    #m.EXPORT_SIZE = True
    #m.EXPORT_SPACE = True
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = _example_HandshakedFifo()
    print(to_rtl_str(m))
