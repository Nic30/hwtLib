#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.interfaces.std import Signal, HandshakeSync, VectSignal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwtLib.clocking.clkBuilder import ClkBuilder


class TimerInfoTest(Unit):
    """
    .. hwt-schematic::
    """
    def _declr(self):
        addClkRstn(self)

        self.tick1 = Signal()._m()
        self.tick2 = Signal()._m()
        self.tick16 = Signal()._m()

        self.tick17 = Signal()._m()
        self.tick34 = Signal()._m()

        self.tick256 = Signal()._m()

        self.tick384 = Signal()._m()

    def _impl(self):
        tick1, tick2, tick16, tick17, tick34, tick256, tick384 =\
            ClkBuilder(self, self.clk)\
            .timers([1, 2, 16, 17, 34, 256, 384])
        self.tick1(tick1)
        self.tick2(tick2)
        self.tick16(tick16)

        self.tick17(tick17)
        self.tick34(tick34)

        self.tick256(tick256)
        self.tick384(tick384)


class TimerTestUnit(Unit):
    """
    .. hwt-schematic::
    """

    def _declr(self):
        addClkRstn(self)

        self.tick1 = HandshakeSync()._m()
        self.tick2 = HandshakeSync()._m()
        self.tick16 = HandshakeSync()._m()

        self.tick17 = HandshakeSync()._m()
        self.tick34 = HandshakeSync()._m()

        self.tick256 = HandshakeSync()._m()

        self.tick384 = HandshakeSync()._m()
        self.core = TimerInfoTest()

    def _impl(self):
        propagateClkRstn(self)

        for intf in self._interfaces:
            if intf not in [self.clk, self.rst_n]:
                intf.vld(getattr(self.core, getSignalName(intf)))


class DynamicCounterInstancesExample(Unit):
    """
    .. hwt-schematic::
    """
    def _declr(self):
        addClkRstn(self)
        self.period = VectSignal(10)
        self.en = Signal()
        self.rstCntr = Signal()

        self.cntr0 = Signal()._m()
        self.cntr1 = Signal()._m()

    def _impl(self):
        b = ClkBuilder(self, self.clk)
        self.cntr0(b.timerDynamic(self.period, self.en))
        self.cntr1(b.timerDynamic(self.period, self.en, rstSig=self.rstCntr))


class TimerTC(SimTestCase):
    def test_basic(self):
        u = TimerTestUnit()
        self.compileSimAndStart(u)
        CLK = 2 * 390
        RST = 5

        self.runSim(CLK * 10 * Time.ns)
        self.assertSequenceEqual(u.tick1._ag.data,
                                 [((i + 1) * 10 + RST) * Time.ns
                                  for i in range(CLK - 1)])
        # print(u.tick2._ag.data)
        self.assertSequenceEqual(u.tick2._ag.data,
                                 [((i + 1) * 20 + RST) * Time.ns
                                  for i in range(CLK // 2 - 1)])
        self.assertSequenceEqual(u.tick16._ag.data,
                                 [((i + 1) * 160 + RST) * Time.ns
                                  for i in range(CLK // 16)])
        self.assertSequenceEqual(u.tick17._ag.data,
                                 [((i + 1) * 170 + RST) * Time.ns
                                  for i in range(CLK // 17)])
        self.assertSequenceEqual(u.tick34._ag.data,
                                 [((i + 1) * 340 + RST) * Time.ns
                                  for i in range(CLK // 34)])
        self.assertSequenceEqual(u.tick256._ag.data,
                                 [((i + 1) * 2560 + RST) * Time.ns
                                  for i in range(CLK // 256)])
        self.assertSequenceEqual(u.tick384._ag.data,
                                 [((i + 1) * 3840 + RST) * Time.ns
                                  for i in range(CLK // 384)])

    def test_dynamic_simple(self):
        u = DynamicCounterInstancesExample()

        self.compileSimAndStart(u)

        u.en._ag.data.append(1)
        u.rstCntr._ag.data.extend([0, 0, 0, 0, 1, 1, 1, 0])
        u.period._ag.data.append(5)

        self.runSim(200 * Time.ns)
        self.assertValSequenceEqual(
            u.cntr0._ag.data,
            [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0])
        self.assertValSequenceEqual(
            u.cntr1._ag.data,
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0])


if __name__ == "__main__":
    # from hwt.synthesizer.utils import toRtl
    # u = TimerInfoTest()
    # u = DynamicCounterInstancesExample()
    # print(toRtl(u))

    import unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TimerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
