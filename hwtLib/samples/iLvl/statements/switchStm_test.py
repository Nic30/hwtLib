#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwtLib.samples.iLvl.statements.switchStm import SwitchStmUnit
from hwt.simulator.simTestCase import SimTestCase


class SwitchStmTC(SimTestCase):
    def setUp(self):
        self.u = SwitchStmUnit()
        self.prepareUnit(self.u)

    def test_allCases(self):
        u = self.u
        u.sel._ag.data = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 1]
        u.b._ag.data = [0, 1, 0, 0, 0, 0, 0, 0, 1, None, 0]
        u.c._ag.data = [0, 0, 0, 1, 0, 0, 0, 0, 1, None, 0]
        u.d._ag.data = [0, 0, 0, 0, 0, 1, 0, 0, 1, None, 0]

        self.doSim(200 * Time.ns)

        self.assertSequenceEqual([0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0], agInts(u.a))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(SwitchStmTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
