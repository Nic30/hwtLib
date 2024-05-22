#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceMUX
from hwt.synth import synthesised
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.statements.switchStm import SwitchStmHwModule


class SwitchStmTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_allCases(self):
        self.dut = SwitchStmHwModule()
        self.compileSimAndStart(self.dut)

        dut = self.dut
        dut.sel._ag.data.extend([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 1])
        dut.a._ag.data.extend([0, 1, 0, 0, 0, 0, 0, 0, 1, None, 0])
        dut.b._ag.data.extend([0, 0, 0, 1, 0, 0, 0, 0, 1, None, 0])
        dut.c._ag.data.extend([0, 0, 0, 0, 0, 1, 0, 0, 1, None, 0])

        self.runSim(110 * Time.ns)

        self.assertValSequenceEqual(dut.out._ag.data,
                                    [0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0])

    def test_vhdlSerialization(self):
        self.assert_serializes_as_file(SwitchStmHwModule(), "SwitchStmHwModule.vhd")

    def test_verilogSerialization(self):
        self.assert_serializes_as_file(SwitchStmHwModule(), "SwitchStmHwModule.v")

    def test_systemcSerialization(self):
        self.assert_serializes_as_file(SwitchStmHwModule(), "SwitchStmHwModule.cpp")

    def test_resources(self):
        dut = SwitchStmHwModule()

        expected = {(ResourceMUX, 1, 4): 1}

        s = ResourceAnalyzer()
        synthesised(dut)
        s.visit_HwModule(dut)
        r = s.report()
        self.assertDictEqual(r, expected)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([SwitchStmTC("test_vhdlSerialization")])
    suite = testLoader.loadTestsFromTestCase(SwitchStmTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
