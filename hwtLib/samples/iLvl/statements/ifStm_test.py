#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwtLib.samples.iLvl.statements.ifStm import SimpleIfStatement
from hwt.simulator.simTestCase import SimTestCase


class IfStmTC(SimTestCase):
    def setUp(self):
        self.u = SimpleIfStatement()
        self.prepareUnit(self.u)

    def test_allCases(self):
        u = self.u

        u.a._ag.data = [1, 1, 1, 0, 0, 0, 0, 0]
        u.b._ag.data = [0, 1, None, 0, 1, None, 1, 0]
        u.c._ag.data = [0, 0, 0, 0, 1, 0, 0, 0]

        self.doSim(80 * Time.ns)

        self.assertSequenceEqual([0, 1, None, 0, 1, None, 0, 0], agInts(u.d))


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(IfStmTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
