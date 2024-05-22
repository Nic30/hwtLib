#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hwIOs.std import HwIODataRdVld
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.cdc import HandshakedCdc
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.utils import period_to_freq


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
        dut = cls.dut = HandshakedCdc(HwIODataRdVld)
        dut.DATA_WIDTH = 8
        dut.IN_FREQ = period_to_freq(cls.IN_CLK)
        dut.OUT_FREQ = period_to_freq(cls.OUT_CLK)
        cls.compileSim(dut)

    def setUp(self):
        SimTestCase.setUp(self)
        dut = self.dut
        dut.dataIn_clk._ag.period = self.IN_CLK
        for rst in [dut.dataIn_rst_n, dut.dataOut_rst_n]:
            rst._ag.initDelay += self.IN_CLK

    def test_normalOp(self):
        dut = self.dut
        REF = [1, 2, 3, 4, 5]
        dut.dataIn._ag.data.extend(REF)
        self.runSim(self.slowest_clk() * 40)
        self.assertValSequenceEqual(dut.dataOut._ag.data, REF)

    def test_nop(self):
        dut = self.dut
        self.runSim(self.slowest_clk() * 40)
        self.assertEmpty(dut.dataOut._ag.data)


class HandshakedCdc_fast_to_slow_TC(HandshakedCdc_slow_to_fast_TC):
    IN_CLK = HandshakedCdc_slow_to_fast_TC.OUT_CLK
    OUT_CLK = HandshakedCdc_slow_to_fast_TC.IN_CLK


if __name__ == "__main__":
    _ALL_TCs = [HandshakedCdc_slow_to_fast_TC, HandshakedCdc_fast_to_slow_TC]
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HandshakedCdc_slow_to_fast_TC("test_normalOp")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
