#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import Handshaked
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.reg2 import HandshakedReg2


class HsReg2TC(SimTestCase):
    def setUp(self):
        u = HandshakedReg2(Handshaked)
        self.u, self.model, self.procs = simPrepare(u)
    
    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

        self.doSim(200 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data, [1, 2, 3, 4, 5, 6])  # 1 was in reset
        self.assertValSequenceEqual([], u.dataIn._ag.data)



if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HsRegTC('test_passdata'))
    suite.addTest(unittest.makeSuite(HsReg2TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
