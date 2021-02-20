#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.fifoArray import FifoArray
from pyMathBitPrecise.bit_utils import mask
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import WaitWriteOnly, Timer


class FifoArrayTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = FifoArray()
        u.ITEMS = 4
        cls.compileSim(u)

    def test_nop(self):
        u = self.u
        u.pop._ag.dinData.append(0)  # at leas a single value for preset is required
        self.runSim(16 * CLK_PERIOD)
        self.assertEmpty(u.pop._ag.data)
        self.assertEmpty(u.insert._ag.dinData)

    def test_insert4(self):
        u = self.u
        u.insert._ag.data.extend([
            (0, 0, 10),
            (0, 1, 11),
            (1, 1, 12),
            (2, 1, 13),
        ])
        # u.pop._ag.dinData.extend([0, 1, 0])

        self.runSim(16 * CLK_PERIOD)
        self.assertEmpty(u.pop._ag.data)
        m = self.rtl_simulator.model
        self.assertValEqual(m.io.item_valid.read(), mask(4))
        self.assertValEqual(m.io.item_last.read(), 1 << 3)
        self.assertValSequenceEqual(m.io.values.read(), [10, 11, 12, 13])

    def test_insert3(self):
        u = self.u
        u.insert._ag.data.extend([
            (0, 0, 10),
            (0, 1, 11),
            (1, 1, 12),
        ])

        self.runSim(16 * CLK_PERIOD)
        self.assertEmpty(u.pop._ag.data)
        m = self.rtl_simulator.model
        self.assertValEqual(m.io.item_valid.read(), mask(3))
        self.assertValEqual(m.io.item_last.read(), 1 << 2)
        self.assertValSequenceEqual([m.io.values[i].read() for i in range(3)], [10, 11, 12])

    def test_insert2x2(self):
        u = self.u
        u.insert._ag.data.extend([
            (0, 0, 10),
            (0, 1, 11),
            (0, 0, 12),
            (2, 1, 13),
        ])
        # u.pop._ag.dinData.extend([0, 1, 0])

        self.runSim(16 * CLK_PERIOD)
        self.assertEmpty(u.pop._ag.data)
        m = self.rtl_simulator.model
        self.assertValEqual(m.io.item_valid.read(), mask(4))
        self.assertValEqual(m.io.item_last.read(), (1 << 3) | (1 << 1))
        self.assertValSequenceEqual(m.io.values.read(), [10, 11, 12, 13])

    def test_insert1pop1(self):
        u = self.u
        u.insert._ag.data.extend([
            (0, 0, 10),
        ])
        def pop_control():
            pop = u.pop._ag
            yield WaitWriteOnly()
            pop.setEnable(False)
            yield Timer(4*CLK_PERIOD)
            yield WaitWriteOnly()
            pop.dinData.extend([0])
            pop.setEnable(True)

        self.procs.append(pop_control())

        self.runSim(16 * CLK_PERIOD)
        m = self.rtl_simulator.model
        self.assertValEqual(m.io.item_valid.read(), 0)
        self.assertValEqual(m.io.item_last.read(), 1)
        self.assertValSequenceEqual(u.pop._ag.data, [(10, 1, 0), ])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(FifoArrayTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
