#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwtLib.samples.iLvl.statements.fsm import FsmExample, HadrcodedFsmExample
from hwt.simulator.simTestCase import SimTestCase


class FsmExampleTC(SimTestCase):
    def setUp(self):
        super(FsmExampleTC, self).setUp()
        self.u = FsmExample()
        self.prepareUnit(self.u)

    def test_allCases(self):
        u = self.u

        u.a._ag.data = [1, 1, 1, 0, 0, 0, 0, 0]
        u.b._ag.data = [0, 1, 0, 0, 1, 0, 1, 0]

        self.doSim(80 * Time.ns)

        self.assertSequenceEqual([1, 1, 3, 1, 1, 2, 2, 2], agInts(u.dout))


class HadrcodedFsmExampleTC(FsmExampleTC):
    def setUp(self):
        SimTestCase.setUp(self)
        self.u = HadrcodedFsmExample()
        self.prepareUnit(self.u)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(FsmExampleTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
