#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Clk, VectSignal
from hwt.synthesizer.unit import Unit


class SimpleAsyncRam(Unit):
    """
    Note that there is no such a thing in hw yet...

    .. hwt-schematic::
    """
    def _declr(self):
        self.addr_in = VectSignal(2)
        self.din = VectSignal(8)

        self.addr_out = VectSignal(2)
        self.dout = VectSignal(8)._m()

    def _impl(self):
        self._ram = ram = self._sig("ram_data", Bits(8)[4])
        self.dout(ram[self.addr_out])
        ram[self.addr_in](self.din)


class SimpleSyncRam(SimpleAsyncRam):
    """
    .. hwt-schematic::
    """
    def _declr(self):
        super()._declr()
        self.clk = Clk()

    def _impl(self):
        self._ram = ram = self._sig("ram_data", Bits(8)[4])

        If(self.clk._onRisingEdge(),
           self.dout(ram[self.addr_out]),
           ram[self.addr_in](self.din)
        )


if __name__ == "__main__":  # alias python "main" function
    from hwt.synthesizer.utils import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    u = SimpleAsyncRam()
    print(toRtl(u))
