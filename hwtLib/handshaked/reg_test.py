#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import Handshaked
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.reg import HandshakedReg


class HsRegL1D0TC(SimTestCase):
    LATENCY = 1
    DELAY = 0
    def setUp(self):
        SimTestCase.setUp(self)
        self.u = HandshakedReg(Handshaked)
        self.u.DELAY.set(self.DELAY)
        self.u.LATENCY.set(self.LATENCY)
        self.prepareUnit(self.u)
    
    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

        self.doSim((self.DELAY + self.LATENCY) * 120 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data, [1, 2, 3, 4, 5, 6])
        self.assertValSequenceEqual([], u.dataIn._ag.data)

    def test_r_passdata(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]
        self.randomize(u.dataIn)
        self.randomize(u.dataOut)
        
        self.doSim((self.DELAY + self.LATENCY) * 600 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data, [1, 2, 3, 4, 5, 6])
        self.assertValSequenceEqual([], u.dataIn._ag.data)


class HsRegL2D1TC(HsRegL1D0TC):
    LATENCY = 2
    DELAY = 1

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HsRegTC('test_passdata'))
    suite.addTest(unittest.makeSuite(HsRegL1D0TC))
    suite.addTest(unittest.makeSuite(HsRegL2D1TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
