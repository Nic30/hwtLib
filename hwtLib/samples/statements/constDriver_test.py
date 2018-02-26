#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.statements.constDriver import ConstDriverUnit


class ConstDriverTC(SimTestCase):
    def setUp(self):
        super(ConstDriverTC, self).setUp()
        self.u = ConstDriverUnit()
        self.prepareUnit(self.u)

    def test_simple(self):
        u = self.u
        self.runSim(20 * Time.ns)

        self.assertValSequenceEqual(u.out0._ag.data, [0, 0])
        self.assertValSequenceEqual(u.out1._ag.data, [1, 1])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(ConstDriverTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
