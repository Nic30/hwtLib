#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.axi.simpleAxiRegs import SimpleAxiRegs
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


allMask = mask(32 // 8)


class SimpleAxiRegsTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = SimpleAxiRegs()
        cls.compileSim(cls.dut)

    def test_nop(self):
        dut = self.dut

        self.runSim(25 * CLK_PERIOD)

        self.assertEmpty(dut.axi._ag.r.data)
        self.assertEmpty(dut.axi._ag.b.data)

    def test_falseWrite(self):
        dut = self.dut
        axi = dut.axi._ag

        axi.w.data += [(11, allMask), (37, allMask)]

        self.runSim(25 * CLK_PERIOD)

        self.assertEqual(len(axi.w.data), 2 - 1)
        self.assertEmpty(dut.axi._ag.r.data)
        self.assertEmpty(dut.axi._ag.b.data)

    def test_write(self):
        dut = self.dut
        axi = dut.axi._ag

        axi.aw.data += [(0, 0), (4, 0)]
        axi.w.data += [(11, allMask), (37, allMask)]

        self.runSim(25 * CLK_PERIOD)

        self.assertEmpty(axi.aw.data)
        self.assertEmpty(axi.w.data)
        self.assertEmpty(dut.axi._ag.r.data)
        self.assertEqual(len(dut.axi._ag.b.data), 2)

        model = self.rtl_simulator.model.io

        self.assertValSequenceEqual(
            [model.reg0.val, model.reg1.val],
            [11, 37])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([SimpleAxiRegsTC("test_write")])
    suite = testLoader.loadTestsFromTestCase(SimpleAxiRegsTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
