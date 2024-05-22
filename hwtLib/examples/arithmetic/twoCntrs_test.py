#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.arithmetic.twoCntrs import TwoCntrs
from hwtSimApi.constants import CLK_PERIOD

eightOnes = [1 for _ in range(8)]
eightZeros = [0 for _ in range(8)]


class TwoCntrsTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = TwoCntrs()
        cls.compileSim(cls.dut)

    def test_nothingEnable(self):
        dut = self.dut
        dut.a_en._ag.data.append(0)
        dut.b_en._ag.data.append(0)

        self.runSim(9 * CLK_PERIOD)

        eq = self.assertValSequenceEqual
        eq(dut.eq._ag.data, eightOnes)
        eq(dut.gt._ag.data, eightZeros)
        eq(dut.lt._ag.data, eightZeros)
        eq(dut.ne._ag.data, eightZeros)

    def test_allEnable(self):
        dut = self.dut
        dut.a_en._ag.data.append(1)
        dut.b_en._ag.data.append(1)

        self.runSim(9 * CLK_PERIOD)

        eq = self.assertValSequenceEqual
        eq(dut.eq._ag.data, eightOnes)
        eq(dut.gt._ag.data, eightZeros)
        eq(dut.lt._ag.data, eightZeros)
        eq(dut.ne._ag.data, eightZeros)

    def test_aEnable(self):
        dut = self.dut
        dut.a_en._ag.data.append(1)
        dut.b_en._ag.data.append(0)

        self.runSim(9 * CLK_PERIOD)

        eq = self.assertValSequenceEqual
        eq(dut.eq._ag.data, [1, 0, 0, 0, 0, 0, 0, 0])
        eq(dut.gt._ag.data, [0, 1, 1, 1, 1, 1, 1, 1])
        eq(dut.lt._ag.data, eightZeros)
        eq(dut.ne._ag.data, [0, 1, 1, 1, 1, 1, 1, 1])

    def test_nonValid(self):
        dut = self.dut
        dut.a_en._ag.data.append(None)
        dut.b_en._ag.data.append(None)

        self.runSim(9 * CLK_PERIOD)
        eq = self.assertValSequenceEqual
        eq(dut.eq._ag.data, [1, None, None, None, None, None, None, None])
        eq(dut.gt._ag.data, [0, None, None, None, None, None, None, None])
        eq(dut.lt._ag.data, [0, None, None, None, None, None, None, None])
        eq(dut.ne._ag.data, [0, None, None, None, None, None, None, None])

    def test_withStops(self):
        dut = self.dut
        dut.a_en._ag.data.extend([1, 0, 0, 1])
        dut.b_en._ag.data.extend([1, 1, 0, 0, 1])

        self.runSim(9 * CLK_PERIOD)

        eq = self.assertValSequenceEqual
        eq(dut.eq._ag.data, [1, 1, 0, 0, 1, 1, 1, 1])
        eq(dut.gt._ag.data, eightZeros)
        eq(dut.lt._ag.data, [0, 0, 1, 1, 0, 0, 0, 0])
        eq(dut.ne._ag.data, [0, 0, 1, 1, 0, 0, 0, 0])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([TwoCntrsTC("test_aEnable")])
    suite = testLoader.loadTestsFromTestCase(TwoCntrsTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
