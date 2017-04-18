#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwtLib.samples.iLvl.statements.constDriver import ConstDriverUnit
from hwt.simulator.simTestCase import SimTestCase


class ConstDriverTC(SimTestCase):
    def setUp(self):
        super(ConstDriverTC, self).setUp()
        self.u = ConstDriverUnit()
        self.prepareUnit(self.u)

    def test_simple(self):
        u = self.u
        self.doSim(20 * Time.ns)

        self.assertSequenceEqual([0], agInts(u.out0))
        self.assertSequenceEqual([1], agInts(u.out1))


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(ConstDriverTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
