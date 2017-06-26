#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import connect
from hwt.interfaces.std import Signal, Clk, VectSignal
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.mem.ram import Ram_dp


class GroupOfBlockrams(Unit):
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

            self.out_w_a = extData()
            self.out_w_b = extData()
            self.out_r_a = extData()
            self.out_r_b = extData()

            with self._paramsShared():
                self.bramR = Ram_dp()
                self.bramW = Ram_dp()

    def _impl(self):
        s = self
        bramR = s.bramR
        bramW = s.bramW

        all_bram_ports = [bramR.a, bramR.b, bramW.a, bramW.b]

        connect(s.clk, *map(lambda i: i.clk, all_bram_ports))
        connect(s.en, *map(lambda i: i.en, all_bram_ports))
        connect(s.we, *map(lambda i: i.we, all_bram_ports))
        connect(s.addr, *map(lambda i: i.addr, all_bram_ports))

        bramW.a.din ** s.in_w_a
        bramW.b.din ** s.in_w_b
        bramR.a.din ** s.in_r_a
        bramR.b.din ** s.in_r_b
        s.out_w_a ** bramW.a.dout
        s.out_w_b ** bramW.b.dout
        s.out_r_a ** bramR.a.dout
        s.out_r_b ** bramR.b.dout


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(GroupOfBlockrams))
