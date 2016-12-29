#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.code import If
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.shortcuts import toRtl


class NopValSample(Unit):
    def _declr(self):
        addClkRstn(self)
        self.en = Signal()
        self.dout = Signal()
    
    def _impl(self):
        cntr = self._reg("cntr", vecT(8), 0)
    
        If(self.en,
          cntr ** (cntr + 1) 
        )
        self.dout ** cntr[7]
    
if __name__ == "__main__":
    u = NopValSample()
    print(toRtl(u))
