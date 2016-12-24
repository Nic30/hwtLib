#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.code import If
from hwt.synthesizer.interfaceLevel.unit import Unit


class SelfRefCntr(Unit):
    def _declr(self):
        self.dt = vecT(8, False)
        
        addClkRstn(self)
        
        self.dout = Signal(dtype=self.dt)
            
    def _impl(self):
        cntr = self._reg("cntr", self.dt, defVal=0)
        
        If(cntr._eq(4),
           cntr ** 0
        ).Else(
           cntr ** (cntr + 1)
        )
        
        self.dout ** cntr
        
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(SelfRefCntr()))

