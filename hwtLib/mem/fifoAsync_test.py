#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import Time
from hwtLib.mem.fifoAsync import FifoAsync
from hwtLib.mem.fifo_test import FifoTC


class FifoAsyncTC(FifoTC):
    IN_CLK = 30 * Time.ns
    CLK = max(FifoTC.OUT_CLK, IN_CLK)
    ITEMS = 4

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = FifoAsync()
        dut.DATA_WIDTH = 8
        dut.DEPTH = cls.ITEMS
        cls.compileSim(dut)

    def setUp(self):
        FifoTC.setUp(self)
        self.dut.dataIn_clk._ag.period = self.IN_CLK
        OUT_CLK = self.dut.dataOut_clk._ag.period
        RST_DELAY = int(max(self.IN_CLK, OUT_CLK) * 1.6)
        self.dut.dataIn_rst_n._ag.initDelay = \
            self.dut.dataOut_rst_n._ag.initDelay = RST_DELAY

    def test_tryMore2(self, capturedOffset=0):
        FifoTC.test_tryMore2(self, capturedOffset=capturedOffset)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([FifoAsyncTC("test_tryMore")])
    suite = testLoader.loadTestsFromTestCase(FifoAsyncTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
