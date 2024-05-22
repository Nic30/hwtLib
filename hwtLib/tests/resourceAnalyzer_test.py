#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.code import Switch
from hwt.hdl.operatorDefs import HwtOps
from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal
from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceMUX, \
    ResourceLatch
from hwt.hwModule import HwModule
from hwt.synth import synthesised


class LatchInSwitchTest(HwModule):
    def _declr(self):
        self.a = HwIOVectSignal(4)
        self.b = HwIOVectSignal(4)._m()

    def _impl(self):
        Switch(self.a).add_cases([(i, self.b(i)) for i in range(6)])


class DualLatchInSwitchTest(LatchInSwitchTest):
    def _declr(self):
        super(DualLatchInSwitchTest, self)._declr()
        self.c = HwIOVectSignal(4)._m()

    def _impl(self):
        super(DualLatchInSwitchTest, self)._impl()
        Switch(self.a).add_cases([(i, self.c(i)) for i in range(4)])


class BoolToBitTest(HwModule):
    def _declr(self):
        self.a = HwIOVectSignal(4)
        self.b = HwIOVectSignal(4)
        self.c = HwIOSignal()._m()

    def _impl(self):
        self.c(self.a._eq(self.b))


class ResourceAnalyzer_TC(unittest.TestCase):
    def test_latch_in_switch(self):
        dut = LatchInSwitchTest()
        ra = ResourceAnalyzer()
        synthesised(dut)
        ra.visit_HwModule(dut)
        res = ra.report()
        expected = {
            (ResourceMUX, 4, 6): 1,
            ResourceLatch: 4
            }
        self.assertDictEqual(res, expected)

    def test_dualLatch_in_switch(self):
        dut = DualLatchInSwitchTest()
        ra = ResourceAnalyzer()
        synthesised(dut)
        ra.visit_HwModule(dut)
        res = ra.report()
        expected = {
            (ResourceMUX, 4, 4): 1,
            (ResourceMUX, 4, 6): 1,
            ResourceLatch: 8
            }
        self.assertDictEqual(res, expected)

    def test_BoolToBits(self):
        dut = BoolToBitTest()
        ra = ResourceAnalyzer()
        synthesised(dut)
        ra.visit_HwModule(dut)
        res = ra.report()
        expected = {
            (HwtOps.EQ, 4): 1,
            }
        self.assertDictEqual(res, expected)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([ResourceAnalyzer_TC("test_BoolToBits")])
    suite = testLoader.loadTestsFromTestCase(ResourceAnalyzer_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
