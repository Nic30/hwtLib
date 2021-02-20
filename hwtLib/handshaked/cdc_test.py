#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.interfaces.std import Handshaked
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.cdc import HandshakedCdc
from hwtSimApi.constants import CLK_PERIOD, Time


def T_to_f(time):
    """
    Period to frequency
    """
    return 1e9 / (time / Time.ns)


class HandshakedCdc_slow_to_fast_TC(SimTestCase):
    IN_CLK = 3 * CLK_PERIOD
    OUT_CLK = CLK_PERIOD

    def slowest_clk(self):
        """
        Return clk period of slowest clock
        """
        return max(self.IN_CLK, self.OUT_CLK)

    @classmethod
    def setUpClass(cls):
        u = cls.u = HandshakedCdc(Handshaked)
        u.DATA_WIDTH = 8
        u.IN_FREQ = T_to_f(cls.IN_CLK)
        u.OUT_FREQ = T_to_f(cls.OUT_CLK)
        cls.compileSim(u)

    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u
        u.dataIn_clk._ag.period = self.IN_CLK
        for rst in [u.dataIn_rst_n, u.dataOut_rst_n]:
            rst._ag.initDelay += self.IN_CLK

    def test_normalOp(self):
        u = self.u
        REF = [1, 2, 3, 4, 5]
        u.dataIn._ag.data.extend(REF)
        self.runSim(self.slowest_clk() * 40)
        self.assertValSequenceEqual(u.dataOut._ag.data, REF)

    def test_nop(self):
        u = self.u
        self.runSim(self.slowest_clk() * 40)
        self.assertEmpty(u.dataOut._ag.data)


class HandshakedCdc_fast_to_slow_TC(HandshakedCdc_slow_to_fast_TC):
    IN_CLK = HandshakedCdc_slow_to_fast_TC.OUT_CLK
    OUT_CLK = HandshakedCdc_slow_to_fast_TC.IN_CLK


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HandshakedCdcTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(HandshakedCdc_slow_to_fast_TC))
    suite.addTest(unittest.makeSuite(HandshakedCdc_fast_to_slow_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
