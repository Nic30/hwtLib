#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.examples.arithmetic.twoCntrs import TwoCntrs
from pycocotb.constants import CLK_PERIOD

eightOnes = [1 for _ in range(8)]
eightZeros = [0 for _ in range(8)]


class TwoCntrsTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        return TwoCntrs()

    def test_nothingEnable(self):
        u = self.u
        u.a_en._ag.data.append(0)
        u.b_en._ag.data.append(0)

        self.runSim(9 * CLK_PERIOD)

        eq = self.assertValSequenceEqual
        eq(u.eq._ag.data, eightOnes)
        eq(u.gt._ag.data, eightZeros)
        eq(u.lt._ag.data, eightZeros)
        eq(u.ne._ag.data, eightZeros)

    def test_allEnable(self):
        u = self.u
        u.a_en._ag.data.append(1)
        u.b_en._ag.data.append(1)

        self.runSim(9 * CLK_PERIOD)

        eq = self.assertValSequenceEqual
        eq(u.eq._ag.data, eightOnes)
        eq(u.gt._ag.data, eightZeros)
        eq(u.lt._ag.data, eightZeros)
        eq(u.ne._ag.data, eightZeros)

    def test_aEnable(self):
        u = self.u
        u.a_en._ag.data.append(1)
        u.b_en._ag.data.append(0)

        self.runSim(9 * CLK_PERIOD)

        eq = self.assertValSequenceEqual
        eq(u.eq._ag.data, [1, 0, 0, 0, 0, 0, 0, 0])
        eq(u.gt._ag.data, [0, 1, 1, 1, 1, 1, 1, 1])
        eq(u.lt._ag.data, eightZeros)
        eq(u.ne._ag.data, [0, 1, 1, 1, 1, 1, 1, 1])

    def test_nonValid(self):
        u = self.u
        u.a_en._ag.data.append(None)
        u.b_en._ag.data.append(None)

        self.runSim(9 * CLK_PERIOD)
        eq = self.assertValSequenceEqual
        eq(u.eq._ag.data, [1, None, None, None, None, None, None, None])
        eq(u.gt._ag.data, [0, None, None, None, None, None, None, None])
        eq(u.lt._ag.data, [0, None, None, None, None, None, None, None])
        eq(u.ne._ag.data, [0, None, None, None, None, None, None, None])

    def test_withStops(self):
        u = self.u
        u.a_en._ag.data.extend([1, 0, 0, 1])
        u.b_en._ag.data.extend([1, 1, 0, 0, 1])

        self.runSim(9 * CLK_PERIOD)

        eq = self.assertValSequenceEqual
        eq(u.eq._ag.data, [1, 1, 0, 0, 1, 1, 1, 1])
        eq(u.gt._ag.data, eightZeros)
        eq(u.lt._ag.data, [0, 0, 1, 1, 0, 0, 0, 0])
        eq(u.ne._ag.data, [0, 0, 1, 1, 0, 0, 0, 0])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_aEnable'))
    suite.addTest(unittest.makeSuite(TwoCntrsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
