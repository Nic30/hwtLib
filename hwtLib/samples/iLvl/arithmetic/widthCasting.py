#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.interfaces.std import VectSignal
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.vectorUtils import fitTo
from hdl_toolkit.synthesizer.codeOps import connect


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
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    
    u = WidthCastingExample()
    print(toRtl(u))
