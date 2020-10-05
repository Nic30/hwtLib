#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Handshaked
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.handshaked.reg import HandshakedReg
from pycocotb.constants import CLK_PERIOD


class HsRegL1D0TC(SingleUnitSimTestCase):
    LATENCY = 1
    DELAY = 0

    @classmethod
    def getUnit(cls):
        cls.u = HandshakedReg(Handshaked)
        cls.u.DELAY = cls.DELAY
        cls.u.LATENCY = cls.LATENCY
        cls.MAX_LATENCY = cls.LATENCY if isinstance(cls.LATENCY, int) else max(cls.LATENCY)
        return cls.u

    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])

        self.runSim((self.DELAY + self.MAX_LATENCY) * 12 * CLK_PERIOD)

        self.assertValSequenceEqual(u.dataOut._ag.data, [1, 2, 3, 4, 5, 6])
        self.assertValSequenceEqual([], u.dataIn._ag.data)

    def test_r_passdata(self):
        u = self.u
        u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])
        self.randomize(u.dataIn)
        self.randomize(u.dataOut)

        self.runSim((self.DELAY + self.MAX_LATENCY) * 60 * CLK_PERIOD)

        self.assertValSequenceEqual(u.dataOut._ag.data, [1, 2, 3, 4, 5, 6])
        self.assertValSequenceEqual([], u.dataIn._ag.data)


class HsRegL2D1TC(HsRegL1D0TC):
    LATENCY = 2
    DELAY = 1


class HsRegL1_2D0TC(HsRegL1D0TC):
    LATENCY = (1, 2)
    DELAY = 0


HsRegTCs = [
    HsRegL1D0TC, 
    HsRegL2D1TC,
    HsRegL1_2D0TC,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HsRegL1D0TC('test_r_passdata'))
    for tc in HsRegTCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
