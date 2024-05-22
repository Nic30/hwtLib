#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOClk, HwIOVectSignal
from hwt.hwModule import HwModule


class SimpleRom(HwModule):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.addr = HwIOVectSignal(2)
        self.dout = HwIOVectSignal(8)._m()

    def _impl(self):
        rom = self._sig("rom_data", HBits(8)[4], def_val=[1, 2, 3, 4])
        self.dout(rom[self.addr])


class SimpleSyncRom(SimpleRom):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        super()._declr()
        self.clk = HwIOClk()

    def _impl(self):
        rom = self._sig("rom_data", HBits(8)[4], def_val=[1, 2, 3, 4])

        If(self.clk._onRisingEdge(),
           self.dout(rom[self.addr])
        )


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(SimpleSyncRom()))
