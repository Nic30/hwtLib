#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.vectorUtils import fitTo
from hwt.code import connect


class WidthCastingExample(Unit):
    """
    Demonstration of how HWT width conversions are serialized into HDL
    """
    def _declr(self):
        addClkRstn(self)
        
        self.a = VectSignal(8)
        self.b = VectSignal(11)
        
        self.c = VectSignal(12)
        self.d = VectSignal(8)
        
    def _impl(self):
        c = self.c
        a = fitTo(self.a, c)
        b = fitTo(self.b, c)
        
        connect(a + b, c, self.d, fit=True)



if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    
    u = WidthCastingExample()
    print(toRtl(u))
