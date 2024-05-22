#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.operatorDefs import HwtOps
from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceMUX, \
    ResourceFF
from hwt.simulator.utils import HConstSequenceToInts, agentDataToInts
from hwt.synth import synthesised
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.statements.ifStm import SimpleIfStatement, \
    SimpleIfStatement2, SimpleIfStatement2b, SimpleIfStatement2c, \
    SimpleIfStatement3, SimpleIfStatementMergable, \
    SimpleIfStatementMergable1, SimpleIfStatementMergable2, \
    IfStatementPartiallyEnclosed, SimpleIfStatementPartialOverrideNopVal, \
    SimpleIfStatementPartialOverride
from hwtSimApi.constants import CLK_PERIOD



class IfStmTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_SimpleIfStatement(self):
        dut = SimpleIfStatement()
        self.compileSimAndStart(dut)

        dut.a._ag.data.extend([1, 1, 1, 0, 0, 0, 0, 0])
        dut.b._ag.data.extend([0, 1, None, 0, 1, None, 1, 0])
        dut.c._ag.data.extend([0, 0, 0, 0, 1, 0, 0, 0])

        self.runSim(8 * CLK_PERIOD)

        self.assertSequenceEqual(agentDataToInts(dut.d), [0, 1, None, 0, 1, None, 0, 0])

    def test_SimpleIfStatement2(self):
        dut = SimpleIfStatement2()
        self.compileSimAndStart(dut)

        # If(a,
        #     If(b & c,
        #        r(1),
        #     ).Else(
        #        r(0)
        #     )
        # )
        # d(r)

        dut.a._ag.data.extend([1, 1, 1, 0, 0, 0, 1, 0, 1, 0])
        dut.b._ag.data.extend([0, 1, None, 0, 1, None, 1, 0, 0, 0])
        dut.c._ag.data.extend([0, 0, 0, 0, 1, 0, 1, 0, 1, 0])
        expected_dd = [      0, 0, 0, 0, 0, 0, 0, 1, 1, 0]

        self.runSim(11 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.d._ag.data, expected_dd)

    def test_SimpleIfStatement2b(self):
        dut = SimpleIfStatement2b()
        self.compileSimAndStart(dut)
        # If(a & b,
        #     If(c,
        #        r(1),
        #     )
        # ).Elif(c,
        #     r(0)
        # )
        # d(r)

        dut.a._ag.data.extend([1, 1, 1, 0, 0, 0, 1, 0, 1, 0])
        dut.b._ag.data.extend([0, 1, None, 0, 1, None, 1, 0, 0, 0])
        dut.c._ag.data.extend([0, 0, 0, 0, 1, 0, 1, 0, 1, 0])
        expected_dd = [   0, 0, 0, None, None, 0, 0, 1, 1, 0]

        self.runSim(11 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.d._ag.data, expected_dd)

    def test_SimpleIfStatement2c(self):
        dut = SimpleIfStatement2c()
        self.compileSimAndStart(dut)
        # If(a & b,
        #     If(c,
        #        r(0),
        #     )
        # ).Elif(c,
        #     r(1)
        # ).Else(
        #     r(2)
        # )
        # d(r)

        dut.a._ag.data.extend([0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0])
        dut.b._ag.data.extend([0, 0, 1, None, 0, 1, None, 1, 0, 0, 0])
        dut.c._ag.data.extend([1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0])
        expected_dd = [0, 1, 2, 2, None, 2, 1, 2, 0, 2]

        self.runSim(11 * CLK_PERIOD)
        self.assertValSequenceEqual(dut.d._ag.data, expected_dd)

    def test_resources_SimpleIfStatement2c(self):
        dut = SimpleIfStatement2c()

        expected = {
            (HwtOps.AND, 1): 1,
            (HwtOps.EQ, 1): 1,
            (ResourceMUX, 2, 2): 1,
            (ResourceMUX, 2, 4): 1,
            ResourceFF: 2,
        }

        s = ResourceAnalyzer()
        synthesised(dut)
        s.visit_HwModule(dut)
        r = s.report()
        self.assertDictEqual(r, expected)

    def test_SimpleIfStatement3(self):
        dut = SimpleIfStatement3()
        self.compileSimAndStart(dut)

        dut.a._ag.data.extend([0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0])
        dut.b._ag.data.extend([0, 0, 1, None, 0, 1, None, 1, 0, 0, 0])
        dut.c._ag.data.extend([1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0])
        expected_dd = [0 for _ in range(11)]

        self.runSim(11 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.d._ag.data, expected_dd)

    def test_resources_SimpleIfStatement3(self):
        m = SimpleIfStatement3()

        expected = {
        }

        s = ResourceAnalyzer()
        synthesised(m)
        s.visit_HwModule(m)
        r = s.report()
        self.assertDictEqual(r, expected)

    def test_SimpleIfStatementMergable_vhdl(self):
        self.assert_serializes_as_file(SimpleIfStatementMergable,
                                       "SimpleIfStatementMergable.vhd")

    def test_SimpleIfStatementMergable1_vhdl(self):
        self.assert_serializes_as_file(SimpleIfStatementMergable1,
                                       "SimpleIfStatementMergable1.vhd")

    def test_SimpleIfStatementMergable2_vhdl(self):
        self.assert_serializes_as_file(SimpleIfStatementMergable2,
                                       "SimpleIfStatementMergable2.vhd")

    def test_IfStatementPartiallyEnclosed_vhdl(self):
        self.assert_serializes_as_file(IfStatementPartiallyEnclosed,
                                       "IfStatementPartiallyEnclosed.vhd")

    def test_SimpleIfStatementPartialOverride(self):
        self.assert_serializes_as_file(SimpleIfStatementPartialOverride(),
                                       "SimpleIfStatementPartialOverride.vhd")

    def test_SimpleIfStatementPartialOverrideNopVal_vhdl(self):
        self.assert_serializes_as_file(SimpleIfStatementPartialOverrideNopVal,
                                       "SimpleIfStatementPartialOverrideNopVal.vhd")


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([IfStmTC("test_resources_SimpleIfStatement2c")])
    suite = testLoader.loadTestsFromTestCase(IfStmTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
