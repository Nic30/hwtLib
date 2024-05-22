#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hwIOs.std import HwIODataRdVld
from hwtLib.handshaked.fifoAsync import HsFifoAsync
from hwtLib.handshaked.fifo_test import HsFifoTC


class HsFifoAsyncTC(HsFifoTC):
    IN_CLK = 30 * Time.ns
    CLK = max(IN_CLK, HsFifoTC.OUT_CLK)
    ITEMS = 5

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = HsFifoAsync(HwIODataRdVld)
        dut.DATA_WIDTH = 8
        dut.DEPTH = cls.ITEMS
        cls.compileSim(dut)

    def setUp(self):
        HsFifoTC.setUp(self)
        dut = self.dut
        dut.dataIn_clk._ag.period = self.IN_CLK
        for rst in [dut.dataIn_rst_n, dut.dataOut_rst_n]:
            rst._ag.initDelay += self.IN_CLK

    def test_tryMore2(self, capturedOffset=0):
        # capturedOffset=1 because handshaked aget can act in same clk
        super(HsFifoTC, self).test_tryMore2(capturedOffset=capturedOffset)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HsFifoAsyncTC("test_stuckedData")])
    suite = testLoader.loadTestsFromTestCase(HsFifoAsyncTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
