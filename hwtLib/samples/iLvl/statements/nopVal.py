#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.synthesizer.codeOps import If
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.shortcuts import toRtl


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
