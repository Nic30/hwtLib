#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.vectorUtils import fitTo
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class WidthCastingExample(HwModule):
    """
    Demonstration of how HWT width conversions are serialized into HDL

    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        addClkRstn(self)

        self.a = HwIOVectSignal(8)
        self.b = HwIOVectSignal(11)

        self.c = HwIOVectSignal(12)._m()
        self.d = HwIOVectSignal(8)._m()

    @override
    def hwImpl(self):
        c = self.c
        a = fitTo(self.a, c)
        b = fitTo(self.b, c)

        for dst in [c, self.d]:
            dst(a + b, fit=True)


class WidthCastingExampleTC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = WidthCastingExample()
        cls.compileSim(cls.dut)

    def test_basic(self):
        a = 255
        b = 1 << 10
        c = 1 << 11

        dut = self.dut
        dut.a._ag.data.append(a)
        dut.b._ag.data.append(b)
        dut.c._ag.data.append(c)

        self.runSim(2 * CLK_PERIOD)
        d = (a + b + c) & mask(8)
        self.assertValSequenceEqual(dut.d._ag.data, [d, ])


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = WidthCastingExample()
    print(to_rtl_str(m))
