#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Clk, Rst_n
from hwt.code import If
from hwt.synthesizer.interfaceLevel.unit import Unit


class ClkDiv3(Unit):
    """
    @attention: this clock divider implementation suits well for generating of output clock
                inside fpga you should use clocking primitives
                (http://www.xilinx.com/support/documentation/ip_documentation/clk_wiz/v5_1/pg065-clk-wiz.pdf)
    """
    def _declr(self):
        self.clk = Clk()
        self.rst_n = Rst_n()

        self.clkOut = Clk()
    
    def _impl(self):
        r_cnt = self._cntx.sig("r_cnt", typ=vecT(2))    
        f_cnt = self._cntx.sig("f_cnt", typ=vecT(2))    
        rise = self._cntx.sig("rise")
        fall = self._cntx.sig("fall")
        
        rst = self.rst_n._isOn()
        If(rst,
           r_cnt ** 0,
           rise ** 1,
           f_cnt ** 2,
           fall ** 1
        ).Else(
            If(self.clk._onRisingEdge(),
                If(r_cnt._eq(2),
                    r_cnt ** 0,
                    rise ** ~rise
                ).Else(
                    r_cnt ** (r_cnt + 1),
                )
            ),
            If(self.clk._onFallingEdge(),
                If(f_cnt._eq(2),
                    f_cnt ** 0,
                    fall ** ~fall
                ).Else(
                    f_cnt ** (f_cnt + 1),
                )
            )
        )
        
        self.clkOut ** fall._eq(rise)

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(ClkDiv3))
