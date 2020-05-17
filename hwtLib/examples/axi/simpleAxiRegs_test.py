#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.examples.axi.simpleAxiRegs import SimpleAxiRegs
from pyMathBitPrecise.bit_utils import mask
from pycocotb.constants import CLK_PERIOD


allMask = mask(32 // 8)


class SimpleAxiRegsTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        return SimpleAxiRegs()

    def test_nop(self):
        u = self.u

        self.runSim(25 * CLK_PERIOD)

        self.assertEmpty(u.axi._ag.r.data)
        self.assertEmpty(u.axi._ag.b.data)

    def test_falseWrite(self):
        u = self.u
        axi = u.axi._ag

        axi.w.data += [(11, allMask), (37, allMask)]

        self.runSim(25 * CLK_PERIOD)

        self.assertEqual(len(axi.w.data), 2 - 1)
        self.assertEmpty(u.axi._ag.r.data)
        self.assertEmpty(u.axi._ag.b.data)

    def test_write(self):
        u = self.u
        axi = u.axi._ag

        axi.aw.data += [(0, 0), (4, 0)]
        axi.w.data += [(11, allMask), (37, allMask)]

        self.runSim(25 * CLK_PERIOD)

        self.assertEmpty(axi.aw.data)
        self.assertEmpty(axi.w.data)
        self.assertEmpty(u.axi._ag.r.data)
        self.assertEqual(len(u.axi._ag.b.data), 2)

        model = self.rtl_simulator.model.io

        self.assertValSequenceEqual(
            [model.reg0.val, model.reg1.val],
            [11, 37])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(SimpleAxiRegsTC('test_write'))
    suite.addTest(unittest.makeSuite(SimpleAxiRegsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
