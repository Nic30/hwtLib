#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.fifoAsync import FifoAsync
from hwtLib.mem.fifo_test import FifoTC


class FifoAsyncTC(FifoTC):
    IN_CLK = 30 * Time.ns
    CLK = max(FifoTC.OUT_CLK, IN_CLK)
    ITEMS = 4

    @classmethod
    def setUpClass(cls):
        u = cls.u = FifoAsync()
        u.DATA_WIDTH = 8
        u.DEPTH = cls.ITEMS
        cls.compileSim(u)

    def setUp(self):
        FifoTC.setUp(self)
        self.u.dataIn_clk._ag.period = self.IN_CLK
        OUT_CLK = self.u.dataOut_clk._ag.period
        RST_DELAY = int(max(self.IN_CLK, OUT_CLK) * 1.6)
        self.u.dataIn_rst_n._ag.initDelay = \
            self.u.dataOut_rst_n._ag.initDelay = RST_DELAY

    def test_tryMore2(self, capturedOffset=0):
        FifoTC.test_tryMore2(self, capturedOffset=capturedOffset)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoAsyncTC('test_tryMore'))
    suite.addTest(unittest.makeSuite(FifoAsyncTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
