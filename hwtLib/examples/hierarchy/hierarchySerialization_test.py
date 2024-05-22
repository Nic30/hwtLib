#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.hierarchy.extractHierarchyExamples import HwModuleWidthDynamicallyGeneratedSubunitsForRegisters, \
    HwModuleWidthDynamicallyGeneratedSubunitsForRegistersWithExpr, HwModuleWidthDynamicallyGeneratedSubunitsForManyRegisters
from hwtLib.examples.hierarchy.groupOfBlockrams import GroupOfBlockrams
from hwtLib.examples.hierarchy.netFilter import NetFilter
from hwtLib.examples.hierarchy.rippleadder import RippleAdder0, \
    RippleAdder1, RippleAdder2, RippleAdder3
from hwtLib.examples.simpleHwModuleWithHwParam import SimpleHwModuleWithHwParam


class SimpleHwModuleWithParamWithIrrelevantParamAndAnotherParam(SimpleHwModuleWithHwParam):

    @override
    def hwConfig(self):
        SimpleHwModuleWithHwParam.hwConfig(self)
        self.IRELEVANT_PARAM = HwParam(10)
        self.ADDR_WIDTH = HwParam(10)

    @override
    def hwDeclr(self):
        SimpleHwModuleWithHwParam.hwDeclr(self)
        self.a_addr = HwIOVectSignal(self.ADDR_WIDTH)
        self.b_addr = HwIOVectSignal(self.ADDR_WIDTH)._m()

    @override
    def hwImpl(self):
        SimpleHwModuleWithHwParam.hwImpl(self)
        self.b_addr(self.a_addr)


class HierarchySerializationTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_NetFilter_vhdl(self):
        m = NetFilter()
        self.assert_serializes_as_file(m, "netFilter.vhd")

    def test_NetFilter_verilog(self):
        m = NetFilter()
        self.assert_serializes_as_file(m, "netFilter.v")

    def test_NetFilter_systemc(self):
        m = NetFilter()
        self.assert_serializes_as_file(m, "netFilter.cpp")

    def test_groupOfBlockrams_vhdl(self):
        m = GroupOfBlockrams()
        self.assert_serializes_as_file(m, "GroupOfBlockrams.vhd")

    def test_RippleAdder0_verilog(self):
        m = RippleAdder0()
        self.assert_serializes_as_file(m, "RippleAdder0.v")

    def test_RippleAdder0_vhdl(self):
        m = RippleAdder0()
        self.assert_serializes_as_file(m, "RippleAdder0.vhd")

    def test_RippleAdder1_verilog(self):
        m = RippleAdder1()
        self.assert_serializes_as_file(m, "RippleAdder1.v")

    def test_RippleAdder2_verilog(self):
        m = RippleAdder2()
        self.assert_serializes_as_file(m, "RippleAdder2.v")

    def test_RippleAdder3_verilog(self):
        m = RippleAdder3()
        self.assert_serializes_as_file(m, "RippleAdder3.v")

    def test_HwModuleWidthDynamicallyGeneratedSubunitsForRegisters_vhdl(self):
        m = HwModuleWidthDynamicallyGeneratedSubunitsForRegisters()
        self.assert_serializes_as_file(m, "HwModuleWidthDynamicallyGeneratedSubunitsForRegisters.vhd")

    def test_HwModuleWidthDynamicallyGeneratedSubunitsForRegisters_verilog(self):
        m = HwModuleWidthDynamicallyGeneratedSubunitsForRegisters()
        self.assert_serializes_as_file(m, "HwModuleWidthDynamicallyGeneratedSubunitsForRegisters.v")
        
    def test_HwModuleWidthDynamicallyGeneratedSubunitsForRegistersWithExpr_vhdl(self):
        m = HwModuleWidthDynamicallyGeneratedSubunitsForRegistersWithExpr()
        self.assert_serializes_as_file(m, "HwModuleWidthDynamicallyGeneratedSubunitsForRegistersWithExpr.vhd")

    def test_HwModuleWidthDynamicallyGeneratedSubunitsForRegistersWithExpr_verilog(self):
        m = HwModuleWidthDynamicallyGeneratedSubunitsForRegistersWithExpr()
        self.assert_serializes_as_file(m, "HwModuleWidthDynamicallyGeneratedSubunitsForRegistersWithExpr.v")

    def test_HwModuleWidthDynamicallyGeneratedSubunitsForManyRegisters_vhdl(self):
        m = HwModuleWidthDynamicallyGeneratedSubunitsForManyRegisters()
        self.assert_serializes_as_file(m, "HwModuleWidthDynamicallyGeneratedSubunitsForManyRegisters.vhd")

    def test_HwModuleWidthDynamicallyGeneratedSubunitsForManyRegisters_verilog(self):
        m = HwModuleWidthDynamicallyGeneratedSubunitsForManyRegisters()
        self.assert_serializes_as_file(m, "HwModuleWidthDynamicallyGeneratedSubunitsForManyRegisters.v")


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HierarchySerializationTC("test_MultiConfigHwModuleWrapper_same_io_type_different_int_param_verilog")])
    suite = testLoader.loadTestsFromTestCase(HierarchySerializationTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
