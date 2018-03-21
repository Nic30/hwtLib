#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdl.constants import Time
from hwt.simulator.agentConnector import valuesToInts
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.axi.simpleAxiRegs import SimpleAxiRegs


allMask = mask(32 // 8)


class SimpleAxiRegsTC(SimTestCase):
    def setUp(self):
        super(SimpleAxiRegsTC, self).setUp()
        self.u = SimpleAxiRegs()
        self.prepareUnit(self.u)

    def test_nop(self):
        u = self.u

        self.runSim(250 * Time.ns)

        self.assertEmpty(u.axi._ag.r.data)
        self.assertEmpty(u.axi._ag.b.data)

    def test_falseWrite(self):
        u = self.u
        axi = u.axi._ag

        axi.w.data += [(11, allMask), (37, allMask)]

        self.runSim(250 * Time.ns)

        self.assertEqual(len(axi.w.data), 2 - 1)
        self.assertEmpty(u.axi._ag.r.data)
        self.assertEmpty(u.axi._ag.b.data)

    def test_write(self):
        u = self.u
        axi = u.axi._ag

        axi.aw.data += [(0, 0), (4, 0)]
        axi.w.data += [(11, allMask), (37, allMask)]

        self.runSim(250 * Time.ns)

        self.assertEmpty(axi.aw.data)
        self.assertEmpty(axi.w.data)
        self.assertEmpty(u.axi._ag.r.data)
        self.assertEqual(len(u.axi._ag.b.data), 2)

        model = self.model

        self.assertEqual(valuesToInts([model.reg0._oldVal, model.reg1._oldVal]),
                         [11, 37])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(SimpleAxiRegsTC('test_write'))
    suite.addTest(unittest.makeSuite(SimpleAxiRegsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
