#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SimTestCase
from hwtSimApi.constants import CLK_PERIOD
from hwtLib.examples.arithmetic.privateSignals import PrivateSignalsOfStructType


class PrivateSignalsOfStructTypeTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = PrivateSignalsOfStructType()
        cls.compileSim(cls.dut)

    def test_pass_data(self):
        dut = self.dut
        dut.a._ag.data.extend(range(30))
        dut.c._ag.data.extend(range(30))

        self.runSim(30 * CLK_PERIOD)

        eq = self.assertValSequenceEqual
        eq(dut.b._ag.data, list(range(30 - 1)))
        eq(dut.d._ag.data, list(range(6, -1, -1)) + list(range(30 - 6 - 2)))


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([PrivateSignalsOfStructTypeTC("test_pass_data")])
    suite = testLoader.loadTestsFromTestCase(PrivateSignalsOfStructTypeTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
