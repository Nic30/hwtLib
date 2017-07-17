#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwtLib.samples.statements.ifStm import SimpleIfStatement,\
    SimpleIfStatement2, SimpleIfStatement2b, SimpleIfStatement2c
from hwt.simulator.simTestCase import SimTestCase


class IfStmTC(SimTestCase):

    def test_SimpleIfStatement(self):
        u = SimpleIfStatement()
        self.prepareUnit(u)

        u.a._ag.data.extend([1, 1, 1, 0, 0, 0, 0, 0])
        u.b._ag.data.extend([0, 1, None, 0, 1, None, 1, 0])
        u.c._ag.data.extend([0, 0, 0, 0, 1, 0, 0, 0])

        self.doSim(80 * Time.ns)

        self.assertSequenceEqual([0, 1, None, 0, 1, None, 0, 0], agInts(u.d))

    def test_SimpleIfStatement2(self):
        u = SimpleIfStatement2()
        self.prepareUnit(u)

        #If(a,
        #    If(b & c,
        #       r ** 1,
        #    ).Else(
        #       r ** 0
        #    )
        #)
        #d ** r

        u.a._ag.data.extend([1, 1, 1,    0, 0, 0,    1, 0, 1, 0])
        u.b._ag.data.extend([0, 1, None, 0, 1, None, 1, 0, 0, 0])
        u.c._ag.data.extend([0, 0, 0,    0, 1, 0,    1, 0, 1, 0])
        expected_dd =       [0, 0, 0,    0, 0, 0,    0, 1, 1, 0]

        self.doSim(100 * Time.ns)

        self.assertValSequenceEqual(u.d._ag.data, expected_dd)

    def test_SimpleIfStatement2b(self):
        u = SimpleIfStatement2b()
        self.prepareUnit(u)
        #If(a & b,
        #    If(c,
        #       r ** 1,
        #    )
        #).Elif(c,
        #    r ** 0
        #)
        #d ** r

        u.a._ag.data.extend([1, 1, 1,    0, 0, 0,    1, 0, 1, 0])
        u.b._ag.data.extend([0, 1, None, 0, 1, None, 1, 0, 0, 0])
        u.c._ag.data.extend([0, 0, 0,    0, 1, 0,    1, 0, 1, 0])
        expected_dd =       [0, 0, 0,    0, 0, 0,    0, 1, 1, 0]

        self.doSim(100 * Time.ns)

        self.assertValSequenceEqual(u.d._ag.data, expected_dd)

    def test_SimpleIfStatement2c(self):
        u = SimpleIfStatement2c()
        self.prepareUnit(u)
        #If(a & b,
        #    If(c,
        #       r ** 0,
        #    )
        #).Elif(c,
        #    r ** 1
        #).Else(
        #    r ** 2
        #)
        #d ** r

        u.a._ag.data.extend([0, 1, 1, 1,    0,    0, 0,    1, 0, 1, 0])
        u.b._ag.data.extend([0, 0, 1, None, 0,    1, None, 1, 0, 0, 0])
        u.c._ag.data.extend([1, 0, 0, 0,    0,    1, 0,    1, 0, 1, 0])
        expected_dd =       [0, 0, 2, 2,    None, 2, 1,    2, 0, 2]

        self.doSim(100 * Time.ns)

        self.assertValSequenceEqual(u.d._ag.data, expected_dd)

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(IfStmTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
