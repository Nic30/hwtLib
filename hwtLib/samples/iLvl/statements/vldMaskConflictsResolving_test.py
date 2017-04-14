#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.iLvl.statements.vldMaskConflictsResolving import VldMaskConflictsResolving


class VldMaskConflictsResolvingTC(SimTestCase):
    def setUp(self):
        self.u = VldMaskConflictsResolving()
        self.prepareUnit(self.u)

    def test_allCases(self):
        u = self.u
        u.a._ag.data = [0, 1, None, 0, 0, 0, 0, 0, 1, None, 0]
        u.b._ag.data = [0, 0, 0, 1, None, 0, 0, 0, 1, None, 0]

        self.doSim(200 * Time.ns)

        self.assertSequenceEqual([0, 0, 0, 1, None, 0, 1, None, 0], agInts(u.c))


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(VldMaskConflictsResolvingTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
