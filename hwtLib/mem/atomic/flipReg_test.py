#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.atomic.flipReg import FlipRegister


class FlipRegTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = FlipRegister()
        cls.compileSim(cls.u)

    def test_simpleWriteAndSwitch(self):
        u = self.u

        # u.select_sig._ag.initDelay = 6 * Time.ns
        u.select_sig._ag.data.extend([0, 0, 0, 1, 0])
        u.first._ag.dout.append(1)
        u.second._ag.dout.append(2)

        self.runSim(90 * Time.ns)

        self.assertValSequenceEqual(u.first._ag.din,
                                    [0, 1, 1, 2, 1, 1, 1, 1])
        self.assertValSequenceEqual(u.second._ag.din,
                                    [0, 2, 2, 1, 2, 2, 2, 2])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([FlipRegTC("test_withStops")])
    suite = testLoader.loadTestsFromTestCase(FlipRegTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
