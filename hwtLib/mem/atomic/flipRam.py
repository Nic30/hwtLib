#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.interfaces.std import Signal, BramPort_withoutClk, Clk
from hwt.interfaces.utils import propagateClk
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.unit import Unit
from hwtLib.mem.ram import RamSingleClock


@serializeParamsUniq
class FlipRam(Unit):
    """
    Switchable RAM, there are two memories and two sets of ports,
    Each set of ports is every time connected to opposite ram.
    By select you can choose between RAMs.

    This component is meant to be form of synchronization.
    Example first RAM is connected to first set of ports, writer performs actualizations on first RAM
    and reader reads data from second ram by second set of ports.

    Then select is set and access is flipped. Reader now has access to RAM 0 and writer to RAM 1.

    .. hwt-autodoc::
    """

    def _config(self):
        RamSingleClock._config(self)

    def _declr(self):
        PORT_CNT = self.PORT_CNT

        with self._paramsShared():
            self.clk = Clk()

            # to let IDEs resolve type of port
            self.firstA = BramPort_withoutClk()
            self.secondA = BramPort_withoutClk()

            if PORT_CNT == 2:
                self.firstB = BramPort_withoutClk()
                self.secondB = BramPort_withoutClk()
            elif PORT_CNT > 2:
                raise NotImplementedError()

            self.select_sig = Signal()

            self.ram0 = RamSingleClock()
            self.ram1 = RamSingleClock()

    def _impl(self):
        propagateClk(self)
        PORT_CNT = self.PORT_CNT

        fa = self.firstA
        sa = self.secondA

        If(self.select_sig,
           self.ram0.port[0](fa),
           self.ram1.port[0](sa)
        ).Else(
           self.ram0.port[0](sa),
           self.ram1.port[0](fa) 
        )
        if PORT_CNT == 2:
            fb = self.firstB
            sb = self.secondB
            If(self.select_sig,
               self.ram0.port[1](fb),
               self.ram1.port[1](sb),
            ).Else(
               self.ram0.port[1](sb),
               self.ram1.port[1](fb)
            )
        elif PORT_CNT > 2:
            raise NotImplementedError()


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    print(to_rtl_str(FlipRam()))
