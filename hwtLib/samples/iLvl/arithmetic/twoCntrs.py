#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.code import If
from hwt.synthesizer.interfaceLevel.unit import Unit


class TwoCntrs(Unit):
    def _declr(self):
        addClkRstn(self)
        
        self.a_en = Signal()
        self.b_en = Signal()
        
        self.eq = Signal()
        self.ne = Signal()
        self.lt = Signal()
        self.gt = Signal()
        

    def _impl(self):
        index_t = vecT(8, False)
        
        a = self._reg("reg_a", index_t, defVal=0)
        b = self._reg("reg_b", index_t, defVal=0)
        
        If(self.a_en,
           a ** (a + 1)
        )
        
        If(self.b_en,
           b ** (b + 1)
        )
        
        self.eq ** a._eq(b)
        self.ne ** (a != b)
        self.lt ** (a < b) 
        self.gt ** (a > b) 


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    
    u = TwoCntrs()
    print(toRtl(u))
