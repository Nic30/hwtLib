#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.fork import HandshakedFork


class HsForkWithReference(HandshakedFork):
    def _declr(self):
        HandshakedFork._declr(self)
        addClkRstn(self)


class HsForkTC(SimTestCase):
    def setUp(self):
        super(HsForkTC, self).setUp()
        self.u = HsForkWithReference(Handshaked)
        self.u.DATA_WIDTH.set(4)
        self.prepareUnit(self.u)

    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

        self.doSim(150 * Time.ns)

        self.assertValSequenceEqual(u.dataOut[0]._ag.data, [1, 2, 3, 4, 5, 6])
        self.assertValSequenceEqual(u.dataOut[1]._ag.data, [1, 2, 3, 4, 5, 6])

        self.assertSequenceEqual([], u.dataIn._ag.data)


class HsFork_randomized_TC(HsForkTC):
    def setUp(self):
        super(HsFork_randomized_TC, self).setUp()
        self.randomize(self.u.dataIn)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(HsFork_randomized_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
