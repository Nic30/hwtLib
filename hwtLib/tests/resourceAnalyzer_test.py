#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.code import Switch
from hwt.hdl.operatorDefs import AllOps
from hwt.interfaces.std import VectSignal, Signal
from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceMUX, \
    ResourceLatch
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import synthesised


class LatchInSwitchTest(Unit):
    def _declr(self):
        self.a = VectSignal(4)
        self.b = VectSignal(4)._m()

    def _impl(self):
        Switch(self.a).add_cases([(i, self.b(i)) for i in range(6)])


class DualLatchInSwitchTest(LatchInSwitchTest):
    def _declr(self):
        super(DualLatchInSwitchTest, self)._declr()
        self.c = VectSignal(4)._m()

    def _impl(self):
        super(DualLatchInSwitchTest, self)._impl()
        Switch(self.a).add_cases([(i, self.c(i)) for i in range(4)])


class BoolToBitTest(Unit):
    def _declr(self):
        self.a = VectSignal(4)
        self.b = VectSignal(4)
        self.c = Signal()._m()

    def _impl(self):
        self.c(self.a._eq(self.b))


class ResourceAnalyzer_TC(unittest.TestCase):
    def test_latch_in_switch(self):
        u = LatchInSwitchTest()
        ra = ResourceAnalyzer()
        synthesised(u)
        ra.visit_Unit(u)
        res = ra.report()
        expected = {
            (ResourceMUX, 4, 6): 1,
            ResourceLatch: 4
            }
        self.assertDictEqual(res, expected)

    def test_dualLatch_in_switch(self):
        u = DualLatchInSwitchTest()
        ra = ResourceAnalyzer()
        synthesised(u)
        ra.visit_Unit(u)
        res = ra.report()
        expected = {
            (ResourceMUX, 4, 4): 1,
            (ResourceMUX, 4, 6): 1,
            ResourceLatch: 8
            }
        self.assertDictEqual(res, expected)

    def test_BoolToBits(self):
        u = BoolToBitTest()
        ra = ResourceAnalyzer()
        synthesised(u)
        ra.visit_Unit(u)
        res = ra.report()
        expected = {
            (AllOps.EQ, 4): 1,
            }
        self.assertDictEqual(res, expected)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(ResourceAnalyzer_TC('test_BoolToBits'))
    suite.addTest(unittest.makeSuite(ResourceAnalyzer_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
