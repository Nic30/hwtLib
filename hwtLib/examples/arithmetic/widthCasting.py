#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import connect
from hwt.interfaces.std import VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.vectorUtils import fitTo
from pyMathBitPrecise.bit_utils import mask
from pycocotb.constants import CLK_PERIOD


class WidthCastingExample(Unit):
    """
    Demonstration of how HWT width conversions are serialized into HDL

    .. hwt-schematic::
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

        connect(a + b, c, self.d, fit=True)


class WidthCastingExampleTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        return WidthCastingExample()

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
    from hwt.synthesizer.utils import toRtl

    u = WidthCastingExample()
    print(toRtl(u))
