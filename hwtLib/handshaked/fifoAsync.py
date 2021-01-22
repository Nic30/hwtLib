#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Clk, Rst_n, VectSignal
from hwt.math import log2ceil, isPow2
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
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
    def _config(self):
        HandshakedFifo._config(self)
        self.IN_FREQ = Param(int(100e6))
        self.OUT_FREQ = Param(int(100e6))

    def _declr(self):
        assert isPow2(self.DEPTH - 1), (
            "DEPTH has to be 2**n + 1"
            " because fifo has have DEPTH 2**n"
            " and 1 item is stored on output reg", self.DEPTH)
        self.dataIn_clk = Clk()
        self.dataOut_clk = Clk()
        with self._paramsShared():
            with self._associated(clk=self.dataIn_clk):
                self.dataIn_rst_n = Rst_n()
                with self._associated(rst=self.dataIn_rst_n):
                    self.dataIn = self.intfCls()

            with self._associated(clk=self.dataOut_clk):
                self.dataOut_rst_n = Rst_n()
                with self._associated(rst=self.dataOut_rst_n):
                    self.dataOut = self.intfCls()._m()

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
            self.size = VectSignal(SIZE_W, signed=False)
        if self.EXPORT_SPACE:
            self.space = VectSignal(SIZE_W, signed=False)

    def _impl(self):
        HandshakedFifo._impl(
            self,
            clk_rst=(
                (self.dataIn_clk, self.dataIn_rst_n),
                (self.dataOut_clk, self.dataOut_rst_n)
            )
        )


def _example_HsFifoAsync():
    from hwt.interfaces.std import Handshaked
    u = HsFifoAsync(Handshaked)
    u.DEPTH = 5
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_HsFifoAsync()
    print(to_rtl_str(u))
