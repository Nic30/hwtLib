#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import connect
from hwt.interfaces.std import Signal, Clk, VectSignal
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.mem.ram import RamMultiClock


class GroupOfBlockrams(Unit):
    """
    .. hwt-schematic::
    """
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        with self._paramsShared():
            def extData():
                return VectSignal(self.DATA_WIDTH)

            self.clk = Clk()
            self.en = Signal()
            self.we = Signal()

            self.addr = VectSignal(self.ADDR_WIDTH)
            self.in_w_a = extData()
            self.in_w_b = extData()
            self.in_r_a = extData()
            self.in_r_b = extData()

            self.out_w_a = extData()._m()
            self.out_w_b = extData()._m()
            self.out_r_a = extData()._m()
            self.out_r_b = extData()._m()

            with self._paramsShared():
                r = self.bramR = RamMultiClock()
                w = self.bramW = RamMultiClock()
                r.PORT_CNT = w.PORT_CNT = 2

    def _impl(self):
        s = self
        bramR = s.bramR
        bramW = s.bramW

        all_bram_ports = [*bramR.port, *bramW.port]

        connect(s.clk, *[i.clk for i in all_bram_ports])
        connect(s.en, *[i.en for i in all_bram_ports])
        connect(s.we, *[i.we for i in all_bram_ports])
        connect(s.addr, *[i.addr for i in all_bram_ports])

        bramW.port[0].din(s.in_w_a)
        bramW.port[1].din(s.in_w_b)
        bramR.port[0].din(s.in_r_a)
        bramR.port[1].din(s.in_r_b)
        s.out_w_a(bramW.port[0].dout)
        s.out_w_b(bramW.port[1].dout)
        s.out_r_a(bramR.port[0].dout)
        s.out_r_b(bramR.port[1].dout)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    print(to_rtl_str(GroupOfBlockrams()))
