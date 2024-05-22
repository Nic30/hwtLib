#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hwIOs.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.logic.oneHotToBin import OneHotToBin
from hwtSimApi.constants import CLK_PERIOD


class OneHotToBinSimWrap(OneHotToBin):

    def _declr(self):
        OneHotToBin._declr(self)
        addClkRstn(self)


class OneHotToBinTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = OneHotToBinSimWrap()
        cls.ONE_HOT_WIDTH = 8
        dut.ONE_HOT_WIDTH = cls.ONE_HOT_WIDTH
        cls.compileSim(dut)

    def test_nop(self):
        dut = self.dut
        oneHot = dut.oneHot._ag.data
        oneHot.append(0)

        self.runSim(4 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.bin._ag.data, [])

    def test_basic(self):
        dut = self.dut
        oneHot = dut.oneHot._ag.data
        oneHot.append(0)
        for i in range(self.ONE_HOT_WIDTH):
            oneHot.append(1 << i)
        oneHot.append(0)

        self.runSim((self.ONE_HOT_WIDTH + 3) * CLK_PERIOD)

        self.assertValSequenceEqual(dut.bin._ag.data, range(self.ONE_HOT_WIDTH))


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([OneHotToBinTC("test_basic")])
    suite = testLoader.loadTestsFromTestCase(OneHotToBinTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
