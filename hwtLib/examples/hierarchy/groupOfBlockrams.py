#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import connect
from hwt.interfaces.std import Signal, Clk, VectSignal
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.mem.ram import Ram_dp


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
                self.bramR = Ram_dp()
                self.bramW = Ram_dp()

    def _impl(self):
        s = self
        bramR = s.bramR
        bramW = s.bramW

        all_bram_ports = [bramR.a, bramR.b, bramW.a, bramW.b]

        connect(s.clk, *[i.clk for i in all_bram_ports])
        connect(s.en, *[i.en for i in all_bram_ports])
        connect(s.we, *[i.we for i in all_bram_ports])
        connect(s.addr, *[i.addr for i in all_bram_ports])

        bramW.a.din(s.in_w_a)
        bramW.b.din(s.in_w_b)
        bramR.a.din(s.in_r_a)
        bramR.b.din(s.in_r_b)
        s.out_w_a(bramW.a.dout)
        s.out_w_b(bramW.b.dout)
        s.out_r_a(bramR.a.dout)
        s.out_r_b(bramR.b.dout)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(GroupOfBlockrams()))
