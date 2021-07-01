#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.operatorDefs import AllOps
from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceMUX, \
    ResourceFF
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import valuesToInts
from hwt.synthesizer.utils import synthesised
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.statements.ifStm import SimpleIfStatement, \
    SimpleIfStatement2, SimpleIfStatement2b, SimpleIfStatement2c, \
    SimpleIfStatement3, SimpleIfStatementMergable, \
    SimpleIfStatementMergable1, SimpleIfStatementMergable2, \
    IfStatementPartiallyEnclosed, SimpleIfStatementPartialOverrideNopVal, \
    SimpleIfStatementPartialOverride
from hwtSimApi.constants import CLK_PERIOD


def agInts(interface):
    """
    Convert all values which has agent collected in time >=0 to integer array.
    Invalid value will be None.
    """
    return valuesToInts(interface._ag.data)


class IfStmTC(SimTestCase, BaseSerializationTC):
    __FILE__ = __file__

    def test_SimpleIfStatement(self):
        u = SimpleIfStatement()
        self.compileSimAndStart(u)

        u.a._ag.data.extend([1, 1, 1, 0, 0, 0, 0, 0])
        u.b._ag.data.extend([0, 1, None, 0, 1, None, 1, 0])
        u.c._ag.data.extend([0, 0, 0, 0, 1, 0, 0, 0])

        self.runSim(8 * CLK_PERIOD)

        self.assertSequenceEqual([0, 1, None, 0, 1, None, 0, 0], agInts(u.d))

    def test_SimpleIfStatement2(self):
        u = SimpleIfStatement2()
        self.compileSimAndStart(u)

        # If(a,
        #     If(b & c,
        #        r(1),
        #     ).Else(
        #        r(0)
        #     )
        # )
        # d(r)

        u.a._ag.data.extend([1, 1, 1, 0, 0, 0, 1, 0, 1, 0])
        u.b._ag.data.extend([0, 1, None, 0, 1, None, 1, 0, 0, 0])
        u.c._ag.data.extend([0, 0, 0, 0, 1, 0, 1, 0, 1, 0])
        expected_dd = [      0, 0, 0, 0, 0, 0, 0, 1, 1, 0]

        self.runSim(11 * CLK_PERIOD)

        self.assertValSequenceEqual(u.d._ag.data, expected_dd)

    def test_SimpleIfStatement2b(self):
        u = SimpleIfStatement2b()
        self.compileSimAndStart(u)
        # If(a & b,
        #     If(c,
        #        r(1),
        #     )
        # ).Elif(c,
        #     r(0)
        # )
        # d(r)

        u.a._ag.data.extend([1, 1, 1, 0, 0, 0, 1, 0, 1, 0])
        u.b._ag.data.extend([0, 1, None, 0, 1, None, 1, 0, 0, 0])
        u.c._ag.data.extend([0, 0, 0, 0, 1, 0, 1, 0, 1, 0])
        expected_dd = [   0, 0, 0, None, None, 0, 0, 1, 1, 0]

        self.runSim(11 * CLK_PERIOD)

        self.assertValSequenceEqual(u.d._ag.data, expected_dd)

    def test_SimpleIfStatement2c(self):
        u = SimpleIfStatement2c()
        self.compileSimAndStart(u)
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

        u.a._ag.data.extend([0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0])
        u.b._ag.data.extend([0, 0, 1, None, 0, 1, None, 1, 0, 0, 0])
        u.c._ag.data.extend([1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0])
        expected_dd = [0, 1, 2, 2, None, 2, 1, 2, 0, 2]

        self.runSim(11 * CLK_PERIOD)
        self.assertValSequenceEqual(u.d._ag.data, expected_dd)

    def test_resources_SimpleIfStatement2c(self):
        u = SimpleIfStatement2c()

        expected = {
            (AllOps.AND, 1): 1,
            (AllOps.EQ, 1): 1,
            (ResourceMUX, 2, 2): 1,
            (ResourceMUX, 2, 4): 1,
            ResourceFF: 2,
        }

        s = ResourceAnalyzer()
        synthesised(u)
        s.visit_Unit(u)
        r = s.report()
        self.assertDictEqual(r, expected)

    def test_SimpleIfStatement3(self):
        u = SimpleIfStatement3()
        self.compileSimAndStart(u)

        u.a._ag.data.extend([0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0])
        u.b._ag.data.extend([0, 0, 1, None, 0, 1, None, 1, 0, 0, 0])
        u.c._ag.data.extend([1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0])
        expected_dd = [0 for _ in range(11)]

        self.runSim(11 * CLK_PERIOD)

        self.assertValSequenceEqual(u.d._ag.data, expected_dd)

    def test_resources_SimpleIfStatement3(self):
        u = SimpleIfStatement3()

        expected = {
        }

        s = ResourceAnalyzer()
        synthesised(u)
        s.visit_Unit(u)
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
    suite = unittest.TestSuite()
    # suite.addTest(IfStmTC('test_resources_SimpleIfStatement2c'))
    suite.addTest(unittest.makeSuite(IfStmTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
