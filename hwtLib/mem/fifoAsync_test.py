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

    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u = FifoAsync()
        u.DATA_WIDTH.set(8)
        u.DEPTH.set(self.ITEMS)
        self.prepareUnit(u)
        u.dataIn_clk._ag.period = self.IN_CLK

    def test_tryMore2(self, capturedOffset=1):
        FifoTC.test_tryMore2(self, capturedOffset=capturedOffset)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoAsyncTC('test_fifoSingleWord'))
    suite.addTest(unittest.makeSuite(FifoAsyncTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
