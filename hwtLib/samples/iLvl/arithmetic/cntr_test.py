#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwtLib.samples.iLvl.arithmetic.cntr import Cntr
from hwt.simulator.simTestCase import SimTestCase


class CntrTC(SimTestCase):
    def setUp(self):
        super(CntrTC, self).setUp()
        self.u = Cntr()
        self.prepareUnit(self.u)

    def test_overflow(self):
        u = self.u

        u.en._ag.data = [1]
        self.doSim(90 * Time.ns)
        self.assertSequenceEqual([0, 0, 1, 2, 3, 0, 1, 2, 3], agInts(u.val))

    def test_contingWithStops(self):
        u = self.u

        u.en._ag.data = [1, 0, 1, 1, 0, 0, 0]
        self.doSim(90 * Time.ns)
        self.assertSequenceEqual([0, 0, 0, 1, 2, 2, 2, 2, 2], agInts(u.val))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(CntrTC('test_overflow'))
    suite.addTest(unittest.makeSuite(CntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
