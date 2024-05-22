#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.atomic.flipReg import FlipRegister


class FlipRegTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = FlipRegister()
        cls.compileSim(cls.dut)

    def test_simpleWriteAndSwitch(self):
        dut = self.dut

        # dut.select_sig._ag.initDelay = 6 * Time.ns
        dut.select_sig._ag.data.extend([0, 0, 0, 1, 0])
        dut.first._ag.dout.append(1)
        dut.second._ag.dout.append(2)

        self.runSim(90 * Time.ns)

        self.assertValSequenceEqual(dut.first._ag.din,
                                    [0, 1, 1, 2, 1, 1, 1, 1])
        self.assertValSequenceEqual(dut.second._ag.din,
                                    [0, 2, 2, 1, 2, 2, 2, 2])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([FlipRegTC("test_withStops")])
    suite = testLoader.loadTestsFromTestCase(FlipRegTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
