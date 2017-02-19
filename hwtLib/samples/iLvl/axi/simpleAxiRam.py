#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.code import If
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axiLite_conv import AxiLiteConverter
from hwtLib.interfaces.amba import AxiLite
from hwtLib.mem.ram import RamSingleClock


class SimpleAxiRam(Unit):
    """
    Example of axi lite mapped register and ram
    0x0 - reg0
    0x4 - ram0, size: 1024 words
    
    """
    def _config(self):
        self.ADDR_WIDTH = Param(16)
        self.DATA_WIDTH = Param(32)
        
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.axi = AxiLite()
        
        with self._paramsShared():
            self.conv = AxiLiteConverter([(0x0, "reg0"),
                                          (0x4, "ram0", 512)])
        
        
        self.ram = RamSingleClock()
        self.ram.ADDR_WIDTH.set(9)
        self.ram.DATA_WIDTH.set(self.DATA_WIDTH)
        
    def _impl(self):
        propagateClkRstn(self)
        self.conv.bus ** self.axi
        
        reg0 = self._reg("reg0", vecT(32), defVal=0)
        
        conv = self.conv
        If(conv.reg0.dout.vld,
            reg0 ** conv.reg0.dout.data
        )
        conv.reg0.din ** reg0 
        
        self.ram.a ** conv.ram0 

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = SimpleAxiRam()
    print(toRtl(u))
    
