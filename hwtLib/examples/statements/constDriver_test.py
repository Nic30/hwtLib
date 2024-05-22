#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.statements.constDriver import ConstDriverHwModule


class ConstDriverTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = ConstDriverHwModule()
        cls.compileSim(cls.dut)

    def test_simple(self):
        dut = self.dut
        self.runSim(20 * Time.ns)

        self.assertValSequenceEqual(dut.out0._ag.data, [0, 0])
        self.assertValSequenceEqual(dut.out1._ag.data, [1, 1])


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([ConstDriverTC("test_nothingEnable")])
    suite = testLoader.loadTestsFromTestCase(ConstDriverTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
