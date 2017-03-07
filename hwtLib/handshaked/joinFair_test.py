#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import Handshaked
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.joinFair import HsJoinFairShare
from hwt.simulator.agentConnector import valuesToInts


def dataFn(d):
    return d._ag.data


class HsJoinFair_2inputs_TC(SimTestCase):
    def setUp(self):
        u = self.u = HsJoinFairShare(Handshaked)
        self.INPUTS = 2
        u.INPUTS.set(self.INPUTS)
        u.DATA_WIDTH.set(8)
        u.EXPORT_SELECTED.set(True)
        _, self.model, self.procs = simPrepare(self.u)

    def addToAllInputs(self, n):
        u = self.u
        for i, d in enumerate(u.dataIn):
            d._ag.data = [_i + (n * i) for _i in range(n)]

        expected = []
        for d in zip(*map(dataFn, u.dataIn)):
            expected.extend(d)

        return expected

    def test_passdata(self):
        u = self.u
        expected = self.addToAllInputs(6)

        self.doSim(self.INPUTS * 6 * 20 * Time.ns)

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

        self.doSim(self.INPUTS * 6 * 20 * Time.ns)

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

        self.doSim(120 * Time.ns)

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

        self.doSim(self.INPUTS * N * 50 * Time.ns)

        self.assertEqual(set(valuesToInts(u.dataOut._ag.data)),
                         set(expected))


class HsJoinFair_3inputs_TC(HsJoinFair_2inputs_TC):
    def setUp(self):
        u = self.u = HsJoinFairShare(Handshaked)
        self.INPUTS = 3
        u.INPUTS.set(self.INPUTS)
        u.DATA_WIDTH.set(8)
        _, self.model, self.procs = simPrepare(self.u)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HsJoinFair_2inputs_TC('test_passdata'))
    suite.addTest(unittest.makeSuite(HsJoinFair_2inputs_TC))
    suite.addTest(unittest.makeSuite(HsJoinFair_3inputs_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
