#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.arithmetic.selfRefCntr import SelfRefCntr


class SelfRefCntrTC(SimTestCase):
    def setUp(self):
        super(SelfRefCntrTC, self).setUp()
        self.u = SelfRefCntr()
        self.prepareUnit(self.u)

    def test_overflow(self):
        u = self.u

        self.runSim(90 * Time.ns)
        self.assertSequenceEqual(u.dout._ag.data,
                                 [0, 1, 2, 3, 4, 0, 1, 2])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(SelfRefCntrTC('test_overflow'))
    suite.addTest(unittest.makeSuite(SelfRefCntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
