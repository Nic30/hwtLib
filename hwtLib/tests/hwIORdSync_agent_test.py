#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIODataRd
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.simulator.simTestCase import SimTestCase
from hwtSimApi.constants import CLK_PERIOD
from hwt.pyUtils.typingFuture import override


class RdSyncedPipe(HwModule):
    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.a = HwIODataRd()
        self.b = HwIODataRd()._m()

    @override
    def hwImpl(self):
        self.b(self.a)


class HwIORdSync_agent_TC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = RdSyncedPipe()
        cls.compileSim(cls.dut)

    def test_basic_data_pass(self):
        dut = self.dut

        dut.a._ag.data.extend(range(10))

        self.runSim(12 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.b._ag.data, list(range(10)) + [None])


if __name__ == '__main__':
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HwIORdSync_agent_TC("test_basic_data_pass")])
    suite = testLoader.loadTestsFromTestCase(HwIORdSync_agent_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
