#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIOSignal, HwIOClk, HwIOVectSignal
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule
from hwtLib.mem.ram import RamMultiClock


class GroupOfBlockrams(HwModule):
    """
    .. hwt-autodoc::
    """
    def _config(self):
        self.ADDR_WIDTH = HwParam(8)
        self.DATA_WIDTH = HwParam(64)

    def _declr(self):
        with self._hwParamsShared():
            def extData():
                return HwIOVectSignal(self.DATA_WIDTH)

            self.clk = HwIOClk()
            self.en = HwIOSignal()
            self.we = HwIOSignal()

            self.addr = HwIOVectSignal(self.ADDR_WIDTH)
            self.in_w_a = extData()
            self.in_w_b = extData()
            self.in_r_a = extData()
            self.in_r_b = extData()

            self.out_w_a = extData()._m()
            self.out_w_b = extData()._m()
            self.out_r_a = extData()._m()
            self.out_r_b = extData()._m()

            with self._hwParamsShared():
                r = self.bramR = RamMultiClock()
                w = self.bramW = RamMultiClock()
                r.PORT_CNT = w.PORT_CNT = 2

    def _impl(self):
        s = self
        bramR = s.bramR
        bramW = s.bramW

        all_bram_ports = [*bramR.port, *bramW.port]
        for p in all_bram_ports:
            p.clk(s.clk)
            p.en(s.en)
            p.we(s.we)
            p.addr(s.addr)

        bramW.port[0].din(s.in_w_a)
        bramW.port[1].din(s.in_w_b)
        bramR.port[0].din(s.in_r_a)
        bramR.port[1].din(s.in_r_b)
        s.out_w_a(bramW.port[0].dout)
        s.out_w_b(bramW.port[1].dout)
        s.out_r_a(bramR.port[0].dout)
        s.out_r_b(bramR.port[1].dout)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(GroupOfBlockrams()))
