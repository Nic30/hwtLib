#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.agentConnector import agInts
from hwt.simulator.simTestCase import SimpleSimTestCase
from hwtLib.examples.arithmetic.twoCntrs import TwoCntrs
from pycocotb.constants import CLK_PERIOD


eightOnes = [1 for _ in range(8)]
eightZeros = [0 for _ in range(8)]


class TwoCntrsTC(SimpleSimTestCase):
    UNIT_CLS = TwoCntrs

    def test_nothingEnable(self):
        u = self.u
        u.a_en._ag.data.append(0)
        u.b_en._ag.data.append(0)

        self.runSim(9 * CLK_PERIOD)

        self.assertSequenceEqual(agInts(u.eq), eightOnes)
        self.assertSequenceEqual(agInts(u.gt), eightZeros)
        self.assertSequenceEqual(agInts(u.lt), eightZeros)
        self.assertSequenceEqual(agInts(u.ne), eightZeros)

    def test_allEnable(self):
        u = self.u
        u.a_en._ag.data.append(1)
        u.b_en._ag.data.append(1)

        self.runSim(9 * CLK_PERIOD)
        self.assertSequenceEqual(agInts(u.eq), eightOnes)
        self.assertSequenceEqual(agInts(u.gt), eightZeros)
        self.assertSequenceEqual(agInts(u.lt), eightZeros)
        self.assertSequenceEqual(agInts(u.ne), eightZeros)

    def test_aEnable(self):
        u = self.u
        u.a_en._ag.data.append(1)
        u.b_en._ag.data.append(0)

        self.runSim(9 * CLK_PERIOD)
        self.assertSequenceEqual(agInts(u.eq), [1, 0, 0, 0, 0, 0, 0, 0])
        self.assertSequenceEqual(agInts(u.gt), [0, 1, 1, 1, 1, 1, 1, 1])
        self.assertSequenceEqual(agInts(u.lt), eightZeros)
        self.assertSequenceEqual(agInts(u.ne), [0, 1, 1, 1, 1, 1, 1, 1])

    def test_nonValid(self):
        u = self.u
        u.a_en._ag.data.append(None)
        u.b_en._ag.data.append(None)

        self.runSim(9 * CLK_PERIOD)
        self.assertSequenceEqual(agInts(u.eq), [1, None, None, None, None, None, None, None])
        self.assertSequenceEqual(agInts(u.gt), [0, None, None, None, None, None, None, None])
        self.assertSequenceEqual(agInts(u.lt), [0, None, None, None, None, None, None, None])
        self.assertSequenceEqual(agInts(u.ne), [0, None, None, None, None, None, None, None])

    def test_withStops(self):
        u = self.u
        u.a_en._ag.data.extend([1, 0, 0, 1])
        u.b_en._ag.data.extend([1, 1, 0, 0, 1])

        self.runSim(9 * CLK_PERIOD)
        self.assertSequenceEqual(agInts(u.eq), [1, 1, 0, 0, 1, 1, 1, 1])
        self.assertSequenceEqual(agInts(u.gt), eightZeros)
        self.assertSequenceEqual(agInts(u.lt), [0, 0, 1, 1, 0, 0, 0, 0])
        self.assertSequenceEqual(agInts(u.ne), [0, 0, 1, 1, 0, 0, 0, 0])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_aEnable'))
    suite.addTest(unittest.makeSuite(TwoCntrsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
