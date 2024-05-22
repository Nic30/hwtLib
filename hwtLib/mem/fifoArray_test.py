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
        dut = cls.dut = FifoArray()
        dut.ITEMS = 4
        cls.compileSim(dut)

    def test_nop(self):
        dut = self.dut
        dut.pop._ag.dinData.append(0)  # at leas a single value for preset is required
        self.runSim(16 * CLK_PERIOD)
        self.assertEmpty(dut.pop._ag.data)
        self.assertEmpty(dut.insert._ag.dinData)

    def test_insert4(self):
        dut = self.dut
        dut.insert._ag.data.extend([
            (0, 0, 10),
            (0, 1, 11),
            (1, 1, 12),
            (2, 1, 13),
        ])
        # dut.pop._ag.dinData.extend([0, 1, 0])

        self.runSim(16 * CLK_PERIOD)
        self.assertEmpty(dut.pop._ag.data)
        m = self.rtl_simulator.model
        self.assertValEqual(m.io.item_valid.read(), mask(4))
        self.assertValEqual(m.io.item_last.read(), 1 << 3)
        self.assertValSequenceEqual(m.io.values.read(), [10, 11, 12, 13])

    def test_insert3(self):
        dut = self.dut
        dut.insert._ag.data.extend([
            (0, 0, 10),
            (0, 1, 11),
            (1, 1, 12),
        ])

        self.runSim(16 * CLK_PERIOD)
        self.assertEmpty(dut.pop._ag.data)
        m = self.rtl_simulator.model
        self.assertValEqual(m.io.item_valid.read(), mask(3))
        self.assertValEqual(m.io.item_last.read(), 1 << 2)
        self.assertValSequenceEqual([m.io.values[i].read() for i in range(3)], [10, 11, 12])

    def test_insert2x2(self):
        dut = self.dut
        dut.insert._ag.data.extend([
            (0, 0, 10),
            (0, 1, 11),
            (0, 0, 12),
            (2, 1, 13),
        ])
        # dut.pop._ag.dinData.extend([0, 1, 0])

        self.runSim(16 * CLK_PERIOD)
        self.assertEmpty(dut.pop._ag.data)
        m = self.rtl_simulator.model
        self.assertValEqual(m.io.item_valid.read(), mask(4))
        self.assertValEqual(m.io.item_last.read(), (1 << 3) | (1 << 1))
        self.assertValSequenceEqual(m.io.values.read(), [10, 11, 12, 13])

    def test_insert1pop1(self):
        dut = self.dut
        dut.insert._ag.data.extend([
            (0, 0, 10),
        ])
        def pop_control():
            pop = dut.pop._ag
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
        self.assertValSequenceEqual(dut.pop._ag.data, [(10, 1, 0), ])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([FifoArrayTC("test_withStops")])
    suite = testLoader.loadTestsFromTestCase(FifoArrayTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
