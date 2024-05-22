#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOClk, HwIOVectSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override


class SimpleAsyncRam(HwModule):
    """
    Note that there is no such a thing in hw yet...

    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        self.addr_in = HwIOVectSignal(2)
        self.din = HwIOVectSignal(8)

        self.addr_out = HwIOVectSignal(2)
        self.dout = HwIOVectSignal(8)._m()

    @override
    def hwImpl(self):
        self._ram = ram = self._sig("ram_data", HBits(8)[4])
        self.dout(ram[self.addr_out])
        ram[self.addr_in](self.din)


class SimpleSyncRam(SimpleAsyncRam):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        super().hwDeclr()
        self.clk = HwIOClk()

    @override
    def hwImpl(self):
        self._ram = ram = self._sig("ram_data", HBits(8)[4])

        If(self.clk._onRisingEdge(),
           self.dout(ram[self.addr_out]),
           ram[self.addr_in](self.din)
        )


if __name__ == "__main__":  # alias python "main" function
    from hwt.synth import to_rtl_str
    # there is more of synthesis methods. to_rtl_str() returns formated vhdl string
    m = SimpleAsyncRam()
    print(to_rtl_str(m))
