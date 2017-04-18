#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.iLvl.statements.forLoopCntrl import StaticForLoopCntrl


class StaticForLoopCntrlTC(SimTestCase):
    ITERATIONS = 5
    def setUp(self):
        super(StaticForLoopCntrlTC, self).setUp()
        self.u = StaticForLoopCntrl()
        self.u.ITERATIONS.set(self.ITERATIONS)
        self.prepareUnit(self.u)

    def test_simple(self):
        u = self.u
        u.bodyBreak._ag.data.append(0)
        u.cntrl._ag.data.extend([1 for _ in range(10)])
        
        self.doSim(110 * Time.ns)

        self.assertValSequenceEqual(u.index._ag.data, [4, ] + (2 * [4, 3, 2, 1, 0]))


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(StaticForLoopCntrlTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
