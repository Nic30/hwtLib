#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import Time, NOP
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.atomic.flipCntr import FlipCntr


class FlipCntrTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = FlipCntr()
        cls.compileSim(cls.dut)

    def test_nop(self):
        dut = self.dut

        dut.doIncr._ag.data.extend([0, 0])
        self.runSim(90 * Time.ns)

        self.assertValSequenceEqual(dut.data._ag.din,
                                    [0 for _ in range(8)])

    def test_incr(self):
        dut = self.dut

        dut.doIncr._ag.data.extend([0, 1, 0, 0, 0])
        dut.doFlip._ag.data.extend([NOP, NOP, 1, NOP, NOP])

        self.runSim(90 * Time.ns)

        self.assertValSequenceEqual(
            dut.data._ag.din,
            [0, 0] + [1 for _ in range(6)])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([FlipCntrTC("test_nop")])
    suite = testLoader.loadTestsFromTestCase(FlipCntrTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
