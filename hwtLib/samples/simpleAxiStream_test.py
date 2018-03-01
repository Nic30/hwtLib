#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdl.constants import Time, NOP
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.simpleAxiStream import SimpleUnitAxiStream


class SynchronizedSimpleUnitAxiStream(SimpleUnitAxiStream):
    """
    Unit with reference clk added
    """

    def _declr(self):
        SimpleUnitAxiStream._declr(self)
        addClkRstn(self)


class SimpleUnitAxiStream_TC(SimTestCase):
    def setUp(self):
        super(SimpleUnitAxiStream_TC, self).setUp()
        self.u = SynchronizedSimpleUnitAxiStream()
        self.prepareUnit(self.u)

    def test_nop(self):
        u = self.u
        self.runSim(200 * Time.ns)

        self.assertEqual(len(u.b._ag.data), 0)

    def test_pass(self):
        u = self.u

        u.a._ag.data.extend([(11, mask(u.a.strb._dtype.bit_length()), 1),
                             NOP,
                             (12, mask(u.a.strb._dtype.bit_length()), 1)
                             ])

        self.runSim(200 * Time.ns)
        self.assertEqual(len(u.b._ag.data), 2)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(SimpleUnitAxiStream_TC('test_nop'))
    suite.addTest(unittest.makeSuite(SimpleUnitAxiStream_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
