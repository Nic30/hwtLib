#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal, Clk
from hwt.intfLvl import Param, Unit, c
from hwtLib.mem.ram import Ram_dp


class GroupOfBlockrams(Unit):
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(64)
    
    def _declr(self):
        with self._paramsShared():
            extData = lambda : Signal(dtype=vecT(self.DATA_WIDTH))
            self.clk = Clk()
            self.we = Signal()
            self.addr = Signal(dtype=vecT(self.ADDR_WIDTH))
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
        
        c(s.clk,
            bramR.a.clk, bramR.b.clk,
            bramW.a.clk, bramW.b.clk)
        c(s.we,
            bramR.a.we, bramR.b.we,
            bramW.a.we, bramW.b.we)
        c(self.addr,
            bramR.a.addr, bramR.b.addr,
            bramW.a.addr, bramW.b.addr)
        
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
