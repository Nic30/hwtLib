#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.intfLvl import Param, Unit
from hwtHdlParsers.tests.vhdlCodesign.axiLiteBasicSlave import AxiLiteBasicSlave
from hwtLib.interfaces.amba import  AxiLite


class AxiLiteSlaveContainer(Unit):
    def _config(self):
        self.ADDR_WIDTH = Param(13)
        self.DATA_WIDTH = Param(14)
        
    def _declr(self):
        with self._paramsShared():
            self.slv = AxiLiteBasicSlave()
            self.axi = AxiLite()
        self.slv.C_S_AXI_ADDR_WIDTH.set(self.ADDR_WIDTH)
        self.slv.C_S_AXI_DATA_WIDTH.set(self.DATA_WIDTH)

    def _impl(self):
        self.slv.S_AXI ** self.axi
    
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiLiteSlaveContainer()
    toRtl(u)
    
    print(u.ADDR_WIDTH.get())
    # print(u.slv.C_S_AXI_ADDR_WIDTH.get())
    print(u.slv.S_AXI.ADDR_WIDTH.get())
    print(u.slv.S_AXI.ar.ADDR_WIDTH.get())
    print(u.slv.S_AXI.ar.addr._dtype.bit_length())
    
    print(toRtl(AxiLiteSlaveContainer, "axiLSlvCont"))
