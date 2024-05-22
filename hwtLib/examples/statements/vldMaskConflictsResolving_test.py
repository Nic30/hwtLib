#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.statements.vldMaskConflictsResolving import VldMaskConflictsResolving


class VldMaskConflictsResolvingTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = VldMaskConflictsResolving()
        cls.compileSim(cls.dut)

    def test_allCases(self):
        dut = self.dut
        dut.a._ag.data.extend([0, 1, None, 0, 0, 0, 0, 0, 1, None, 0])
        dut.b._ag.data.extend([0, 0, 0, 1, None, 0, 0, 0, 1, None, 0])

        self.runSim(120 * Time.ns)

        self.assertValSequenceEqual(dut.c._ag.data,
                                    [0, 0, 0, 1, None, 0, 0, 0, 1, None, 0, 0])


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([VldMaskConflictsResolvingTC("test_nothingEnable")])
    suite = testLoader.loadTestsFromTestCase(VldMaskConflictsResolvingTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
