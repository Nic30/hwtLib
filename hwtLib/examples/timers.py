#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hwIOs.std import HwIOSignal, HwIORdVldSync, HwIOVectSignal
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.hwModuleImplHelpers import getSignalName
from hwtLib.clocking.clkBuilder import ClkBuilder


class TimerInfoTest(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        addClkRstn(self)

        self.tick1 = HwIOSignal()._m()
        self.tick2 = HwIOSignal()._m()
        self.tick16 = HwIOSignal()._m()

        self.tick17 = HwIOSignal()._m()
        self.tick34 = HwIOSignal()._m()

        self.tick256 = HwIOSignal()._m()

        self.tick384 = HwIOSignal()._m()

    @override
    def hwImpl(self):
        tick1, tick2, tick16, tick17, tick34, tick256, tick384 = \
            ClkBuilder(self, self.clk)\
            .timers([1, 2, 16, 17, 34, 256, 384])
        self.tick1(tick1)
        self.tick2(tick2)
        self.tick16(tick16)

        self.tick17(tick17)
        self.tick34(tick34)

        self.tick256(tick256)
        self.tick384(tick384)


class TimerTestHwModule(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        addClkRstn(self)

        self.tick1 = HwIORdVldSync()._m()
        self.tick2 = HwIORdVldSync()._m()
        self.tick16 = HwIORdVldSync()._m()

        self.tick17 = HwIORdVldSync()._m()
        self.tick34 = HwIORdVldSync()._m()

        self.tick256 = HwIORdVldSync()._m()

        self.tick384 = HwIORdVldSync()._m()
        self.core = TimerInfoTest()

    @override
    def hwImpl(self):
        propagateClkRstn(self)

        for hwIO in self._hwIOs:
            if hwIO not in (self.clk, self.rst_n):
                hwIO.vld(getattr(self.core, getSignalName(hwIO)))


class DynamicCounterInstancesExample(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.period = HwIOVectSignal(10)
        self.en = HwIOSignal()
        self.rstCntr = HwIOSignal()

        self.cntr0 = HwIOSignal()._m()
        self.cntr1 = HwIOSignal()._m()

    @override
    def hwImpl(self):
        b = ClkBuilder(self, self.clk)
        self.cntr0(b.timerDynamic(self.period, self.en))
        self.cntr1(b.timerDynamic(self.period, self.en, rstSig=self.rstCntr))


class TimerTC(SimTestCase):

    @override
    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def test_basic(self):
        dut = TimerTestHwModule()
        self.compileSimAndStart(dut)
        CLK = 2 * 390
        RST = 5

        self.runSim(CLK * 10 * Time.ns)
        self.assertSequenceEqual(dut.tick1._ag.data,
                                 [((i + 1) * 10 + RST) * Time.ns
                                  for i in range(CLK - 1)])
        # print(dut.tick2._ag.data)
        self.assertSequenceEqual(dut.tick2._ag.data,
                                 [((i + 1) * 20 + RST) * Time.ns
                                  for i in range(CLK // 2 - 1)])
        self.assertSequenceEqual(dut.tick16._ag.data,
                                 [((i + 1) * 160 + RST) * Time.ns
                                  for i in range(CLK // 16)])
        self.assertSequenceEqual(dut.tick17._ag.data,
                                 [((i + 1) * 170 + RST) * Time.ns
                                  for i in range(CLK // 17)])
        self.assertSequenceEqual(dut.tick34._ag.data,
                                 [((i + 1) * 340 + RST) * Time.ns
                                  for i in range(CLK // 34)])
        self.assertSequenceEqual(dut.tick256._ag.data,
                                 [((i + 1) * 2560 + RST) * Time.ns
                                  for i in range(CLK // 256)])
        self.assertSequenceEqual(dut.tick384._ag.data,
                                 [((i + 1) * 3840 + RST) * Time.ns
                                  for i in range(CLK // 384)])

    def test_dynamic_simple(self):
        dut = DynamicCounterInstancesExample()

        self.compileSimAndStart(dut)

        dut.en._ag.data.append(1)
        dut.rstCntr._ag.data.extend([0, 0, 0, 0, 1, 1, 1, 0])
        dut.period._ag.data.append(5)

        self.runSim(200 * Time.ns)
        self.assertValSequenceEqual(
            dut.cntr0._ag.data,
            [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0])
        self.assertValSequenceEqual(
            dut.cntr1._ag.data,
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0])


if __name__ == "__main__":
    # from hwt.synth import to_rtl_str
    # m = TimerInfoTest()
    # m = DynamicCounterInstancesExample()
    # print(to_rtl_str(m))

    import unittest
    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(TimerTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
