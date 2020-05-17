#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import CLK_PERIOD
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.examples.arithmetic.selfRefCntr import SelfRefCntr


class SelfRefCntrTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        return SelfRefCntr()

    def test_overflow(self):
        u = self.u

        self.runSim(9 * CLK_PERIOD)
        self.assertSequenceEqual(u.dout._ag.data,
                                 [0, 1, 2, 3, 4, 0, 1, 2])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(SelfRefCntrTC('test_overflow'))
    suite.addTest(unittest.makeSuite(SelfRefCntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
