#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time, NOP
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.atomic.flipCntr import FlipCntr


class FlipCntrTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = FlipCntr()
        cls.compileSim(cls.u)

    def test_nop(self):
        u = self.u

        u.doIncr._ag.data.extend([0, 0])
        self.runSim(90 * Time.ns)

        self.assertValSequenceEqual(u.data._ag.din,
                                    [0 for _ in range(8)])

    def test_incr(self):
        u = self.u

        u.doIncr._ag.data.extend([0, 1, 0, 0, 0])
        u.doFlip._ag.data.extend([NOP, NOP, 1, NOP, NOP])

        self.runSim(90 * Time.ns)

        self.assertValSequenceEqual(
            u.data._ag.din,
            [0, 0] + [1 for _ in range(6)])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([FlipCntrTC("test_nop")])
    suite = testLoader.loadTestsFromTestCase(FlipCntrTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
