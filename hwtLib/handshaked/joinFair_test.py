#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.interfaces.std import Handshaked
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.handshaked.joinFair import HsJoinFairShare
from hwt.simulator.agentConnector import valuesToInts
from pycocotb.constants import CLK_PERIOD


def dataFn(d):
    return d._ag.data


class HsJoinFair_2inputs_TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = HsJoinFairShare(Handshaked)
        cls.INPUTS = 2
        u.INPUTS = cls.INPUTS
        u.DATA_WIDTH = 8
        u.EXPORT_SELECTED = True
        return u

    def addToAllInputs(self, n):
        u = self.u
        for i, d in enumerate(u.dataIn):
            d._ag.data.extend([_i + (n * i) for _i in range(n)])

        expected = []
        for d in zip(*map(dataFn, u.dataIn)):
            expected.extend(d)

        return expected

    def test_passdata(self):
        u = self.u
        expected = self.addToAllInputs(6)

        self.runSim(self.INPUTS * 6 * 2 * CLK_PERIOD)

        self.assertValSequenceEqual(u.dataOut._ag.data, expected)

        for d in u.dataIn:
            self.assertSequenceEqual([], d._ag.data)

        expSelected = [1 << (i % self.INPUTS) for i in range(self.INPUTS * 6)]
        self.assertValSequenceEqual(u.selectedOneHot._ag.data,
                                    expSelected)

    def test_passdata_oneHasMore(self):
        u = self.u

        expected = self.addToAllInputs(6)

        d = [7, 8, 9, 10, 11, 12]
        u.dataIn[self.INPUTS - 1]._ag.data.extend(d)
        expected.extend(d)

        self.runSim(self.INPUTS * 6 * 2 * CLK_PERIOD)

        self.assertValSequenceEqual(u.dataOut._ag.data, expected)

        for d in u.dataIn:
            self.assertSequenceEqual([], d._ag.data)

        id0 = 1
        id1 = (1 << (self.INPUTS - 1))
        expSelected = [1 << (i % self.INPUTS) for i in range(self.INPUTS * 6)] + 6 * [id1, ]
        self.assertValSequenceEqual(u.selectedOneHot._ag.data,
                                    expSelected)

    def test_passData_onLowPriority(self):
        u = self.u
        lowPriority = u.dataIn[self.INPUTS - 1]
        expected = [_i for _i in range(6)]

        lowPriority._ag.data.extend(expected)

        self.runSim(12 * CLK_PERIOD)

        self.assertValSequenceEqual(u.dataOut._ag.data, expected)

        expSelected = [1 << (self.INPUTS - 1) for _ in range(6)]
        self.assertValSequenceEqual(u.selectedOneHot._ag.data,
                                    expSelected)

    def test_randomized(self):
        u = self.u
        N = 8
        expected = []
        for i, inp in enumerate(u.dataIn):
            self.randomize(inp)
            d = [i * N + i2 + 1 for i2 in range(N)]

            inp._ag.data.extend(d)
            expected.extend(d)

        self.randomize(u.dataOut)

        self.runSim(self.INPUTS * N * 5 * CLK_PERIOD)

        self.assertEqual(set(valuesToInts(u.dataOut._ag.data)),
                         set(expected))


class HsJoinFair_3inputs_TC(HsJoinFair_2inputs_TC):

    @classmethod
    def getUnit(cls):
        u = cls.u = HsJoinFairShare(Handshaked)
        cls.INPUTS = 3
        u.INPUTS = cls.INPUTS
        u.DATA_WIDTH = 8
        return u


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HsJoinFair_2inputs_TC('test_passdata'))
    suite.addTest(unittest.makeSuite(HsJoinFair_2inputs_TC))
    suite.addTest(unittest.makeSuite(HsJoinFair_3inputs_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
