#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Tuple, Union

from hwt.code import If
from hwt.hdl.types.bitsRtlSignal import HBitsRtlSignal
from hwt.hwIOs.std import HwIOVectSignal, HwIOClk, HwIORst_n, HwIORst
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interfaceLevel.utils import HwIO_pack, \
    HwIO_connectPacked
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.mem.fifo import Fifo


@serializeParamsUniq
class HandshakedFifo(HandshakedCompBase):
    """
    Synchronous FIFO for handshaked interfaces
    :note: 1clk to write, 1clk to load to output reg (and then 1clk to read next data).

    .. figure:: ./_static/HandshakedFifo.png

    .. hwt-autodoc:: _example_HandshakedFifo
    """
    FIFO_CLS = Fifo
    REG_CLS = HandshakedReg
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
        assert len(self.INIT_DATA) <= len(self.INIT_DATA)
        self._declr_io()
        DW = self.dataIn._bit_length() - self.NON_DATA_BITS_CNT

        if self.DEPTH > 2:
            f = self.fifo = self.FIFO_CLS()
            f.DATA_WIDTH = DW
            f.DEPTH = self.DEPTH - 1  # because there is an extra register on output

            if len(self.INIT_DATA) == self.DEPTH:
                f.INIT_DATA_FIRST_WORD = self.INIT_DATA[0]
                f.INIT_DATA = self.INIT_DATA[1:]
            else:
                f.INIT_DATA = self.INIT_DATA

            f.EXPORT_SIZE = self.EXPORT_SIZE
            f.EXPORT_SPACE = self.EXPORT_SPACE
        else:
            assert self.REG_CLS is not NotImplementedError, ("register cls is required for selected DEPTH", self.DEPTH)
            # to few items for fifo pointers to work, use registers instead
            r0 = self.REG_CLS(self.HWIO_CLS)
            r0._updateHwParamsFrom(self)
            self.r0 = r0
            if self.DEPTH == 2:
                # the first register must allow for 0 latency so total latency is 1 for write + 1 for read
                #  (and there is no additional latency for copy between regs)
                r0.LATENCY = (0, 1)

                r1 = self.REG_CLS(self.HWIO_CLS)
                r1._updateHwParamsFrom(self)
                self.r1 = r1

    def _connect_size_and_space(self, out_vld: Optional[HBitsRtlSignal], fifo: Optional[Fifo]):
        if self.EXPORT_SIZE:
            size_tmp = self._sig("size_tmp", self.size._dtype)
            size_tmp(fifo.size, fit=True)

            If(out_vld,
               self.size(size_tmp + 1)
            ).Else(
               self.size(size_tmp)
            )

        if self.EXPORT_SPACE:
            space_tmp = self._sig("space_tmp", self.space._dtype)
            space_tmp(fifo.space, fit=True)
            If(out_vld,
               # output register is occupied
               self.space(space_tmp)
            ).Else(
               # output register treated as additional slot in fifo
               self.space(space_tmp + 1)
            )

    def _connect_size_and_space_no_fifo(self):
        """
        variant of :meth:`~._connect_size_and_space` for the case that there is no fifo an registers
        are used instead
        """
        din = self.dataIn
        dout = self.dataIn
        rd = self.get_ready_signal
        vld = self.get_valid_signal
        fifo_read = vld(dout) & rd(dout)
        fifo_write = vld(din) & rd(din)
        if self.EXPORT_SIZE:
            Fifo.constructFifoSizeLogic(self, fifo_read, fifo_write)
        if self.EXPORT_SPACE:
            Fifo.constructFifoSpaceLogic(self, fifo_read, fifo_write)

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

    def _connect_fifo_out(self, out_clk: HwIOClk, out_rst: Optional[Union[HwIORst, HwIORst_n]]):
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
            assert self.DEPTH > 2, (self, self.DEPTH)
            (in_clk, in_rst), (out_clk, out_rst) = clk_rst
            f = self.fifo
            f.dataIn_clk(in_clk)
            f.dataIn_rst_n(in_rst)
            f.dataOut_clk(out_clk)
            f.dataOut_rst_n(out_rst)

        if self.DEPTH == 1:
            if clk_rst is not None:
                raise NotImplementedError()
            self.r0.dataIn(self.dataIn)
            self.dataOut(self.r0.dataOut)
            self._connect_size_and_space_no_fifo()

        elif self.DEPTH == 2:
            if clk_rst is not None:
                raise NotImplementedError()
            self.r0.dataIn(self.dataIn)
            self.r1.dataIn(self.r0.dataOut)
            self.dataOut(self.r1.dataOut)
            self._connect_size_and_space_no_fifo()

        else:
            self._connect_fifo_in()
            out_vld = self._connect_fifo_out(out_clk, out_rst)
            self._connect_size_and_space(out_vld, self.fifo)


def _example_HandshakedFifo():
    from hwt.hwIOs.std import HwIODataRdVld
    m = HandshakedFifo(HwIODataRdVld)
    m.DEPTH = 2
    m.DATA_WIDTH = 4
    # m.EXPORT_SIZE = True
    # m.EXPORT_SPACE = True
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = _example_HandshakedFifo()
    print(to_rtl_str(m))
