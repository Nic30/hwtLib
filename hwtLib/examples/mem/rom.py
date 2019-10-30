#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Clk, VectSignal
from hwt.synthesizer.unit import Unit


class SimpleRom(Unit):
    """
    .. hwt-schematic::
    """
    def _declr(self):
        self.addr = VectSignal(2)
        self.dout = VectSignal(8)._m()

    def _impl(self):
        rom = self._sig("rom_data", Bits(8)[4], def_val=[1, 2, 3, 4])
        self.dout(rom[self.addr])


class SimpleSyncRom(SimpleRom):
    """
    .. hwt-schematic::
    """
    def _declr(self):
        super()._declr()
        self.clk = Clk()

    def _impl(self):
        rom = self._sig("rom_data", Bits(8)[4], def_val=[1, 2, 3, 4])

        If(self.clk._onRisingEdge(),
           self.dout(rom[self.addr])
        )


if __name__ == "__main__":  # alias python main function
    from hwt.synthesizer.utils import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SimpleSyncRom()))
