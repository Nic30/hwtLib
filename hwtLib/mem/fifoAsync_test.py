#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time

from hwtLib.mem.fifoAsync import FifoAsync
from hwtLib.mem.fifo_test import FifoTC


class FifoAsyncTC(FifoTC):
    IN_CLK = 30 * Time.ns
    CLK = max(FifoTC.OUT_CLK, IN_CLK)

    @classmethod
    def getUnit(cls):
        u = cls.u = FifoAsync()
        u.DATA_WIDTH = 8
        u.DEPTH = cls.ITEMS
        return u

    def setUp(self):
        FifoTC.setUp(self)
        self.u.dataIn_clk._ag.period = self.IN_CLK

    def test_tryMore2(self, capturedOffset=1):
        FifoTC.test_tryMore2(self, capturedOffset=capturedOffset)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoAsyncTC('test_fifoSingleWord'))
    suite.addTest(unittest.makeSuite(FifoAsyncTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
