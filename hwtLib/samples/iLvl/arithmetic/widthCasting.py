#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import connect
from hwt.interfaces.std import VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.vectorUtils import fitTo
from hwt.simulator.simTestCase import SimTestCase
from hwt.hdlObjects.constants import Time
from hwt.bitmask import mask


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

class WidthCastingExampleTC(SimTestCase):
    def test_basic(self):
        a = 255
        b = 1 << 10
        c = 1 << 11
        u = WidthCastingExample()
        self.prepareUnit(u)
        
        u.a._ag.data.append(a)
        u.b._ag.data.append(b)
        u.c._ag.data.append(c)
        
        self.doSim(20 * Time.ns)
        d = (a + b + c) & mask(8)
        self.assertValSequenceEqual(u.d._ag.data, [d, ])
        


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl

    u = WidthCastingExample()
    print(toRtl(u))
