#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.vectorUtils import fitTo
from pyMathBitPrecise.bit_utils import mask
from hwtSimApi.constants import CLK_PERIOD


class WidthCastingExample(Unit):
    """
    Demonstration of how HWT width conversions are serialized into HDL

    .. hwt-autodoc::
    """
    def _declr(self):
        addClkRstn(self)

        self.a = VectSignal(8)
        self.b = VectSignal(11)

        self.c = VectSignal(12)._m()
        self.d = VectSignal(8)._m()

    def _impl(self):
        c = self.c
        a = fitTo(self.a, c)
        b = fitTo(self.b, c)

        for dst in [c, self.d]:
            dst(a + b, fit=True)


class WidthCastingExampleTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = WidthCastingExample()
        cls.compileSim(cls.u)

    def test_basic(self):
        a = 255
        b = 1 << 10
        c = 1 << 11

        u = self.u
        u.a._ag.data.append(a)
        u.b._ag.data.append(b)
        u.c._ag.data.append(c)

        self.runSim(2 * CLK_PERIOD)
        d = (a + b + c) & mask(8)
        self.assertValSequenceEqual(u.d._ag.data, [d, ])


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str

    u = WidthCastingExample()
    print(to_rtl_str(u))
