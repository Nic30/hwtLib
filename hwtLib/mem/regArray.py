#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import RegCntrl
from hwt.interfaces.utils import addClkRstn
from hwt.code import If
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam


class RegArray(Unit):
    def _config(self):
        self.ITEMS = Param(4)
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        with self._paramsShared():
            addClkRstn(self)
            self.data = RegCntrl(multipliedBy=self.ITEMS)
    
    def _impl(self):
        regs = self.regs = [self._reg("reg%d" % (i), vecT(self.DATA_WIDTH)) 
                            for i in range(evalParam(self.ITEMS).val)]
        
        for reg, intf in zip(regs, self.data):
            If(intf.dout.vld,
                reg ** intf.dout.data
            )
            
            intf.din ** reg 
        
        

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = RegArray()
    print(toRtl(u))
