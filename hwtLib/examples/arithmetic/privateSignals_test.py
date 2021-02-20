#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SimTestCase
from hwtSimApi.constants import CLK_PERIOD
from hwtLib.examples.arithmetic.privateSignals import PrivateSignalsOfStructType


class PrivateSignalsOfStructTypeTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = PrivateSignalsOfStructType()
        cls.compileSim(cls.u)

    def test_pass_data(self):
        u = self.u
        u.a._ag.data.extend(range(30))
        u.c._ag.data.extend(range(30))

        self.runSim(30 * CLK_PERIOD)

        eq = self.assertValSequenceEqual
        eq(u.b._ag.data, list(range(30 - 1)))
        eq(u.d._ag.data, list(range(6, -1, -1)) + list(range(30 - 6 - 2)))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(PrivateSignalsOfStructTypeTC('test_pass_data'))
    suite.addTest(unittest.makeSuite(PrivateSignalsOfStructTypeTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
