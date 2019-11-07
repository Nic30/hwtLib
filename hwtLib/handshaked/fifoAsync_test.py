#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.interfaces.std import Handshaked

from hwtLib.handshaked.fifoAsync import HsFifoAsync
from hwtLib.handshaked.fifo_test import HsFifoTC
from hwt.hdl.constants import Time


class HsFifoAsyncTC(HsFifoTC):
    IN_CLK = 30 * Time.ns
    CLK = max(IN_CLK, HsFifoTC.OUT_CLK)
    ITEMS = 5

    @classmethod
    def getUnit(cls):
        u = cls.u = HsFifoAsync(Handshaked)
        u.DATA_WIDTH = 8
        u.DEPTH = cls.ITEMS
        return u

    def setUp(self):
        HsFifoTC.setUp(self)
        u = self.u
        u.dataIn_clk._ag.period = self.IN_CLK
        u.rst_n._ag.initDelay += self.IN_CLK

    def test_tryMore2(self, capturedOffset=0):
        # capturedOffset=1 because handshaked aget can act in same clk
        super(HsFifoTC, self).test_tryMore2(capturedOffset=capturedOffset)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HandshakedFifoAsyncTC('test_fifoWriterDisable'))
    # suite.addTest(HandshakedFifoAsyncTC('test_fifoSingleWord'))
    # suite.addTest(HandshakedFifoAsyncTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(HsFifoAsyncTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
