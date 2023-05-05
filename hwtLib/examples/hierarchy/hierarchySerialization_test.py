#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import VectSignal
from hwt.synthesizer.param import Param
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.hierarchy.extractHierarchyExamples import UnitWidthDynamicallyGeneratedSubunitsForRegisters, \
    UnitWidthDynamicallyGeneratedSubunitsForRegistersWithExpr, UnitWidthDynamicallyGeneratedSubunitsForManyRegisters
from hwtLib.examples.hierarchy.groupOfBlockrams import GroupOfBlockrams
from hwtLib.examples.hierarchy.netFilter import NetFilter
from hwtLib.examples.hierarchy.rippleadder import RippleAdder0, \
    RippleAdder1, RippleAdder2, RippleAdder3
from hwtLib.examples.simpleWithParam import SimpleUnitWithParam


class SimpleUnitWithParamWithIrrelevantParamAndAnotherParam(SimpleUnitWithParam):

    def _config(self):
        SimpleUnitWithParam._config(self)
        self.IRELEVANT_PARAM = Param(10)
        self.ADDR_WIDTH = Param(10)

    def _declr(self):
        SimpleUnitWithParam._declr(self)
        self.a_addr = VectSignal(self.ADDR_WIDTH)
        self.b_addr = VectSignal(self.ADDR_WIDTH)._m()

    def _impl(self):
        SimpleUnitWithParam._impl(self)
        self.b_addr(self.a_addr)


class HierarchySerializationTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_NetFilter_vhdl(self):
        u = NetFilter()
        self.assert_serializes_as_file(u, "netFilter.vhd")

    def test_NetFilter_verilog(self):
        u = NetFilter()
        self.assert_serializes_as_file(u, "netFilter.v")

    def test_NetFilter_systemc(self):
        u = NetFilter()
        self.assert_serializes_as_file(u, "netFilter.cpp")

    def test_groupOfBlockrams_vhdl(self):
        u = GroupOfBlockrams()
        self.assert_serializes_as_file(u, "GroupOfBlockrams.vhd")

    def test_RippleAdder0_verilog(self):
        u = RippleAdder0()
        self.assert_serializes_as_file(u, "RippleAdder0.v")

    def test_RippleAdder0_vhdl(self):
        u = RippleAdder0()
        self.assert_serializes_as_file(u, "RippleAdder0.vhd")

    def test_RippleAdder1_verilog(self):
        u = RippleAdder1()
        self.assert_serializes_as_file(u, "RippleAdder1.v")

    def test_RippleAdder2_verilog(self):
        u = RippleAdder2()
        self.assert_serializes_as_file(u, "RippleAdder2.v")

    def test_RippleAdder3_verilog(self):
        u = RippleAdder3()
        self.assert_serializes_as_file(u, "RippleAdder3.v")

    def test_UnitWidthDynamicallyGeneratedSubunitsForRegisters_vhdl(self):
        u = UnitWidthDynamicallyGeneratedSubunitsForRegisters()
        self.assert_serializes_as_file(u, "UnitWidthDynamicallyGeneratedSubunitsForRegisters.vhd")

    def test_UnitWidthDynamicallyGeneratedSubunitsForRegisters_verilog(self):
        u = UnitWidthDynamicallyGeneratedSubunitsForRegisters()
        self.assert_serializes_as_file(u, "UnitWidthDynamicallyGeneratedSubunitsForRegisters.v")
        
    def test_UnitWidthDynamicallyGeneratedSubunitsForRegistersWithExpr_vhdl(self):
        u = UnitWidthDynamicallyGeneratedSubunitsForRegistersWithExpr()
        self.assert_serializes_as_file(u, "UnitWidthDynamicallyGeneratedSubunitsForRegistersWithExpr.vhd")

    def test_UnitWidthDynamicallyGeneratedSubunitsForRegistersWithExpr_verilog(self):
        u = UnitWidthDynamicallyGeneratedSubunitsForRegistersWithExpr()
        self.assert_serializes_as_file(u, "UnitWidthDynamicallyGeneratedSubunitsForRegistersWithExpr.v")

    def test_UnitWidthDynamicallyGeneratedSubunitsForManyRegisters_vhdl(self):
        u = UnitWidthDynamicallyGeneratedSubunitsForManyRegisters()
        self.assert_serializes_as_file(u, "UnitWidthDynamicallyGeneratedSubunitsForManyRegisters.vhd")

    def test_UnitWidthDynamicallyGeneratedSubunitsForManyRegisters_verilog(self):
        u = UnitWidthDynamicallyGeneratedSubunitsForManyRegisters()
        self.assert_serializes_as_file(u, "UnitWidthDynamicallyGeneratedSubunitsForManyRegisters.v")


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HierarchySerializationTC("test_MultiConfigUnitWrapper_same_io_type_different_int_param_verilog")])
    suite = testLoader.loadTestsFromTestCase(HierarchySerializationTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
