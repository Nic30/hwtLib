#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Handshaked
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.reg import HandshakedReg
from hwtSimApi.constants import CLK_PERIOD


class HandshakedRegL1D0TC(SimTestCase):
    LATENCY = 1
    DELAY = 0

    @classmethod
    def setUpClass(cls):
        u = cls.u = HandshakedReg(Handshaked)
        u.DELAY = cls.DELAY
        u.LATENCY = cls.LATENCY
        cls.MAX_LATENCY = cls.LATENCY if isinstance(cls.LATENCY, int) else max(cls.LATENCY)
        cls.compileSim(u)

    def test_passdata(self, N=20):
        u = self.u
        u.dataIn._ag.data.extend(range(N))

        self.runSim((self.DELAY + self.MAX_LATENCY) * 2 * N * CLK_PERIOD)

        self.assertValSequenceEqual(u.dataOut._ag.data, list(range(N)))
        self.assertValSequenceEqual([], u.dataIn._ag.data)

    def test_r_passdata(self, N=20):
        u = self.u
        u.dataIn._ag.data.extend(range(N))
        self.randomize(u.dataIn)
        self.randomize(u.dataOut)

        self.runSim((self.DELAY + self.MAX_LATENCY) * 4 * N * CLK_PERIOD)

        self.assertValSequenceEqual(u.dataOut._ag.data, list(range(N)))
        self.assertValSequenceEqual([], u.dataIn._ag.data)


class HandshakedRegL2D1TC(HandshakedRegL1D0TC):
    LATENCY = 2
    DELAY = 1


class HandshakedRegL1_2D0TC(HandshakedRegL1D0TC):
    LATENCY = (1, 2)
    DELAY = 0


HandshakedRegTCs = [
    HandshakedRegL1D0TC,
    HandshakedRegL2D1TC,
    HandshakedRegL1_2D0TC,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HandshakedRegL1D0TC('test_r_passdata'))
    for tc in HandshakedRegTCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
