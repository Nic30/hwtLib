#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIOClk, HwIORst_n, HwIOVectSignal
from hwt.hwParam import HwParam
from hwt.math import log2ceil, isPow2
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.mem.fifoAsync import FifoAsync


@serializeParamsUniq
class HsFifoAsync(HandshakedFifo):
    """
    Asynchronous FIFO using BRAM/LUT memory, based on:

    :note: same functionality as :class:`hwtLib.handshaked.fifo.HandshakedFifo`
        except it has separated clock for input/output

    .. hwt-autodoc:: _example_HsFifoAsync
    """
    @override
    def hwConfig(self):
        HandshakedFifo.hwConfig(self)
        self.IN_FREQ = HwParam(int(100e6))
        self.OUT_FREQ = HwParam(int(100e6))

    @override
    def hwDeclr(self):
        assert isPow2(self.DEPTH - 1), (
            "DEPTH has to be 2**n + 1"
            " because fifo has have DEPTH 2**n"
            " and 1 item is stored on output reg", self.DEPTH)
        self.dataIn_clk = HwIOClk()
        self.dataOut_clk = HwIOClk()
        with self._hwParamsShared():
            with self._associated(clk=self.dataIn_clk):
                self.dataIn_rst_n = HwIORst_n()
                with self._associated(rst=self.dataIn_rst_n):
                    self.dataIn = self.hwIOCls()

            with self._associated(clk=self.dataOut_clk):
                self.dataOut_rst_n = HwIORst_n()
                with self._associated(rst=self.dataOut_rst_n):
                    self.dataOut = self.hwIOCls()._m()

        f = self.fifo = FifoAsync()
        f.IN_FREQ = self.IN_FREQ
        f.OUT_FREQ = self.OUT_FREQ
        DW = self.dataIn._bit_length() - 2  # 2 for control (valid, ready)
        f.DATA_WIDTH = DW
        # because the output register is used as another item storage
        f.DEPTH = self.DEPTH - 1
        f.EXPORT_SIZE = self.EXPORT_SIZE
        f.EXPORT_SPACE = self.EXPORT_SPACE

        SIZE_W = log2ceil(self.DEPTH + 1 + 1)
        if self.EXPORT_SIZE:
            self.size = HwIOVectSignal(SIZE_W, signed=False)
        if self.EXPORT_SPACE:
            self.space = HwIOVectSignal(SIZE_W, signed=False)

    @override
    def hwImpl(self):
        HandshakedFifo.hwImpl(
            self,
            clk_rst=(
                (self.dataIn_clk, self.dataIn_rst_n),
                (self.dataOut_clk, self.dataOut_rst_n)
            )
        )


def _example_HsFifoAsync():
    from hwt.hwIOs.std import HwIODataRdVld
    
    m = HsFifoAsync(HwIODataRdVld)
    m.DEPTH = 5
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = _example_HsFifoAsync()
    print(to_rtl_str(m))
