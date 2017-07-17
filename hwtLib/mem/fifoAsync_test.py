#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwtLib.mem.fifoAsync import FifoAsync
from hwtLib.mem.fifo_test import FifoTC


class FifoAsyncTC(FifoTC):
    CLK_IN = 30 * Time.ns

    def setUp(self):
        u = self.u = FifoAsync()
        u.DATA_WIDTH.set(8)
        u.DEPTH.set(4)
        self.prepareUnit(u)
        u.dataIn_clk._ag.period = 30 * Time.ns

    def getTime(self, wordCnt):
        return wordCnt * self.CLK_IN

    def test_tryMore(self):
        u = self.u

        u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])
        u.dataOut._ag.enable = False

        self.doSim(self.getTime(12))

        collected = u.dataOut._ag.data

        self.assertValSequenceEqual(self.model.memory._val, [1, 2, 4, 3])
        self.assertValSequenceEqual(collected, [])
        self.assertValSequenceEqual(u.dataIn._ag.data, [5, 6])

    def test_tryMore2(self):
        u = self.u

        u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6, 7, 8])

        def closeOutput(s):
            yield s.wait(self.getTime(3))
            u.dataOut._ag.enable = False

        self.procs.append(closeOutput)
        self.doSim(self.getTime(16))

        collected = u.dataOut._ag.data

        self.assertValSequenceEqual(self.model.memory._val.val, [5, 6, 4, 3])
        self.assertValSequenceEqual(collected, [1, 2])
        self.assertValSequenceEqual(u.dataIn._ag.data, [7, 8])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoAsyncTC('test_fifoSingleWord'))
    suite.addTest(unittest.makeSuite(FifoAsyncTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
