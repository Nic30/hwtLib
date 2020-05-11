#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceMUX
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.utils import synthesised
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.statements.switchStm import SwitchStmUnit


class SwitchStmTC(SimTestCase, BaseSerializationTC):
    __FILE__ = __file__

    def test_allCases(self):
        self.u = SwitchStmUnit()
        self.compileSimAndStart(self.u)

        u = self.u
        u.sel._ag.data.extend([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 1])
        u.a._ag.data.extend([0, 1, 0, 0, 0, 0, 0, 0, 1, None, 0])
        u.b._ag.data.extend([0, 0, 0, 1, 0, 0, 0, 0, 1, None, 0])
        u.c._ag.data.extend([0, 0, 0, 0, 0, 1, 0, 0, 1, None, 0])

        self.runSim(110 * Time.ns)

        self.assertValSequenceEqual(u.out._ag.data,
                                    [0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0])

    def test_vhdlSerialization(self):
        self.assert_serializes_as_file(SwitchStmUnit(), "SwitchStmUnit.vhd")

    def test_verilogSerialization(self):
        self.assert_serializes_as_file(SwitchStmUnit(), "SwitchStmUnit.v")

    def test_systemcSerialization(self):
        self.assert_serializes_as_file(SwitchStmUnit(), "SwitchStmUnit.cpp")

    def test_resources(self):
        u = SwitchStmUnit()

        expected = {(ResourceMUX, 1, 4): 1}

        s = ResourceAnalyzer()
        synthesised(u)
        s.visit_Unit(u)
        r = s.report()
        self.assertDictEqual(r, expected)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(SwitchStmTC('test_vhdlSerialization'))
    suite.addTest(unittest.makeSuite(SwitchStmTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
