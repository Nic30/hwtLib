#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Clk, Rst_n, VectSignal
from hwt.serializer.mode import serializeParamsUniq

from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.mem.fifoAsync import FifoAsync
from hwt.code import log2ceil


@serializeParamsUniq
class HsFifoAsync(HandshakedFifo):
    """
    Asynchronous fifo using BRAM memory, based on:
    http://www.asic-world.com/examples/vhdl/asyn_fifo.html

    :note: same functionality as :class:`hwtLib.handshaked.fifo.HandshakedFifo`
        except it has separated clock for input/output

    .. hwt-schematic:: _example_HsFifoAsync
    """

    def _declr(self):
        self.dataIn_clk = Clk()
        self.dataOut_clk = Clk()
        self.rst_n = Rst_n()

        with self._paramsShared():
            with self._associated(self.dataIn_clk):
                self.dataIn = self.intfCls()

            with self._associated(self.dataOut_clk):
                self.dataOut = self.intfCls()._m()

        f = self.fifo = FifoAsync()
        DW = self.dataIn._bit_length() - 2  # 2 for control (valid, ready)
        f.DATA_WIDTH = DW
        f.DEPTH = self.DEPTH - 1  # because there is an extra register
        f.EXPORT_SIZE = self.EXPORT_SIZE

        if self.EXPORT_SIZE:
            self.size = VectSignal(log2ceil(self.DEPTH + 1 + 1), signed=False)

    def _impl(self):
        HandshakedFifo._impl(self, clks=(self.dataIn_clk, self.dataOut_clk))


def _example_HsFifoAsync():
    from hwt.interfaces.std import Handshaked
    u = HsFifoAsync(Handshaked)
    u.DEPTH = 5
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_HsFifoAsync()
    print(toRtl(u))
