#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.unit import Unit
from hwtLib.examples.statements.forLoopCntrl import StaticForLoopCntrl


class StaticForLoopCntrlTC(SingleUnitSimTestCase):
    ITERATIONS = 5

    @classmethod
    def getUnit(cls) -> Unit:
        u = StaticForLoopCntrl()
        u.ITERATIONS = cls.ITERATIONS
        return u

    def test_simple(self):
        u = self.u
        u.bodyBreak._ag.data.append(0)
        u.cntrl._ag.data.extend([1 for _ in range(10)])

        self.runSim(110 * Time.ns)

        self.assertValSequenceEqual(u.index._ag.data,
                                    (2 * [4, 3, 2, 1, 0]))


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(StaticForLoopCntrlTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
