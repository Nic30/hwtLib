#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import CLK_PERIOD
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.arithmetic.selfRefCntr import SelfRefCntr


class SelfRefCntrTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = SelfRefCntr()
        cls.compileSim(cls.dut)

    def test_overflow(self):
        dut = self.dut

        self.runSim(9 * CLK_PERIOD)
        self.assertSequenceEqual(dut.dout._ag.data,
                                 [0, 1, 2, 3, 4, 0, 1, 2])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([SelfRefCntrTC("test_overflow")])
    suite = testLoader.loadTestsFromTestCase(SelfRefCntrTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
