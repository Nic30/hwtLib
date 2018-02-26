#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.simulator.agentConnector import agInts
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.arithmetic.twoCntrs import TwoCntrs


eightOnes = [1 for _ in range(8)]
eightZeros = [0 for _ in range(8)]


class TwoCntrsTC(SimTestCase):
    def setUp(self):
        super(TwoCntrsTC, self).setUp()
        self.u = TwoCntrs()
        self.prepareUnit(self.u)

    def test_nothingEnable(self):
        u = self.u
        u.a_en._ag.data.append(0)
        u.b_en._ag.data.append(0)

        self.runSim(90 * Time.ns)

        self.assertSequenceEqual(eightOnes, agInts(u.eq))
        self.assertSequenceEqual(eightZeros, agInts(u.gt))
        self.assertSequenceEqual(eightZeros, agInts(u.lt))
        self.assertSequenceEqual(eightZeros, agInts(u.ne))

    def test_allEnable(self):
        u = self.u
        u.a_en._ag.data.append(1)
        u.b_en._ag.data.append(1)

        self.runSim(90 * Time.ns)
        self.assertSequenceEqual(eightOnes, agInts(u.eq))
        self.assertSequenceEqual(eightZeros, agInts(u.gt))
        self.assertSequenceEqual(eightZeros, agInts(u.lt))
        self.assertSequenceEqual(eightZeros, agInts(u.ne))

    def test_aEnable(self):
        u = self.u
        u.a_en._ag.data.append(1)
        u.b_en._ag.data.append(0)

        self.runSim(90 * Time.ns)
        self.assertSequenceEqual([1, 0, 0, 0, 0, 0, 0, 0], agInts(u.eq))
        self.assertSequenceEqual([0, 1, 1, 1, 1, 1, 1, 1], agInts(u.gt))
        self.assertSequenceEqual(eightZeros, agInts(u.lt))
        self.assertSequenceEqual([0, 1, 1, 1, 1, 1, 1, 1], agInts(u.ne))

    def test_nonValid(self):
        u = self.u
        u.a_en._ag.data.append(None)
        u.b_en._ag.data.append(None)

        self.runSim(90 * Time.ns)
        self.assertSequenceEqual([1, None, None, None, None, None, None, None], agInts(u.eq))
        self.assertSequenceEqual([0, None, None, None, None, None, None, None], agInts(u.gt))
        self.assertSequenceEqual([0, None, None, None, None, None, None, None], agInts(u.lt))
        self.assertSequenceEqual([0, None, None, None, None, None, None, None], agInts(u.ne))

    def test_withStops(self):
        u = self.u
        u.a_en._ag.data.extend([1, 0, 0, 1])
        u.b_en._ag.data.extend([1, 1, 0, 0, 1])

        self.runSim(90 * Time.ns)
        self.assertSequenceEqual([1, 1, 0, 0, 1, 1, 1, 1], agInts(u.eq))
        self.assertSequenceEqual(eightZeros, agInts(u.gt))
        self.assertSequenceEqual([0, 0, 1, 1, 0, 0, 0, 0], agInts(u.lt))
        self.assertSequenceEqual([0, 0, 1, 1, 0, 0, 0, 0], agInts(u.ne))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_aEnable'))
    suite.addTest(unittest.makeSuite(TwoCntrsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
