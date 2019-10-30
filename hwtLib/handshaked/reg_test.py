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
        return cls.u

    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])

        self.runSim((self.DELAY + self.LATENCY) * 12 * CLK_PERIOD)

        self.assertValSequenceEqual(u.dataOut._ag.data, [1, 2, 3, 4, 5, 6])
        self.assertValSequenceEqual([], u.dataIn._ag.data)

    def test_r_passdata(self):
        u = self.u
        u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])
        self.randomize(u.dataIn)
        self.randomize(u.dataOut)

        self.runSim((self.DELAY + self.LATENCY) * 60 * CLK_PERIOD)

        self.assertValSequenceEqual(u.dataOut._ag.data, [1, 2, 3, 4, 5, 6])
        self.assertValSequenceEqual([], u.dataIn._ag.data)


class HsRegL2D1TC(HsRegL1D0TC):
    LATENCY = 2
    DELAY = 1


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HsRegL1D0TC('test_r_passdata'))
    suite.addTest(unittest.makeSuite(HsRegL1D0TC))
    suite.addTest(unittest.makeSuite(HsRegL2D1TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
