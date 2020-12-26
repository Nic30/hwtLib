#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import VectSignal
from hwt.synthesizer.param import Param
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.hierarchy.groupOfBlockrams import GroupOfBlockrams
from hwtLib.examples.hierarchy.multiConfigUnit import MultiConfigUnitWrapper
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

    def test_MultiConfigUnitWrapper_same_io_type_different_int_param_vhdl(self):
        u0 = SimpleUnitWithParam()
        u0.DATA_WIDTH = 2
        u1 = SimpleUnitWithParam()
        u1.DATA_WIDTH = 3

        u = MultiConfigUnitWrapper([u0, u1])
        self.assert_serializes_as_file(u, "MultiConfigUnitWrapper_same_io_type_different_int_param.vhd")

    def test_MultiConfigUnitWrapper_same_io_type_different_int_param_verilog(self):
        u0 = SimpleUnitWithParam()
        u0.DATA_WIDTH = 2
        u1 = SimpleUnitWithParam()
        u1.DATA_WIDTH = 3

        u = MultiConfigUnitWrapper([u0, u1])
        self.assert_serializes_as_file(u, "MultiConfigUnitWrapper_same_io_type_different_int_param.v")

    def test_MultiConfigUnitWrapper_3x_same_io_type_different_int_param_vhdl(self):
        u0 = SimpleUnitWithParam()
        u0.DATA_WIDTH = 2
        u1 = SimpleUnitWithParam()
        u1.DATA_WIDTH = 3
        u2 = SimpleUnitWithParam()
        u2.DATA_WIDTH = 4

        u = MultiConfigUnitWrapper([u0, u1, u2])
        self.assert_serializes_as_file(u, "MultiConfigUnitWrapper_3x_same_io_type_different_int_param.vhd")

    def test_MultiConfigUnitWrapper_same_io_type_different_int_param_irrelevant_param_vhdl(self):
        class SimpleUnitWithParamWithIrrelevantParam(SimpleUnitWithParam):
            def _config(self):
                SimpleUnitWithParam._config(self)
                self.IRELEVANT_PARAM = Param(10)

        u0 = SimpleUnitWithParamWithIrrelevantParam()
        u0.DATA_WIDTH = 2
        u1 = SimpleUnitWithParamWithIrrelevantParam()
        u1.DATA_WIDTH = 3

        u = MultiConfigUnitWrapper([u0, u1])
        self.assert_serializes_as_file(u, "MultiConfigUnitWrapper_same_io_type_different_int_param_irrelevant_param.vhd")

    def test_MultiConfigUnitWrapper_same_io_type_different_int_param_irrelevant_param_and_second_param_vhdl(self):
        u0 = SimpleUnitWithParamWithIrrelevantParamAndAnotherParam()
        u0.ADDR_WIDTH = 11
        u0.DATA_WIDTH = 2

        u1 = SimpleUnitWithParamWithIrrelevantParamAndAnotherParam()
        u1.ADDR_WIDTH = 11
        u1.DATA_WIDTH = 3

        u2 = SimpleUnitWithParamWithIrrelevantParamAndAnotherParam()
        u2.ADDR_WIDTH = 13
        u2.DATA_WIDTH = 2

        u3 = SimpleUnitWithParamWithIrrelevantParamAndAnotherParam()
        u3.ADDR_WIDTH = 13
        u3.DATA_WIDTH = 3

        u = MultiConfigUnitWrapper([u0, u1, u2, u3])
        self.assert_serializes_as_file(u, "MultiConfigUnitWrapper_same_io_type_different_int_param_irrelevant_param_and_second_param.vhd")



if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    #suite.addTest(HierarchySerializationTC("test_MultiConfigUnitWrapper_same_io_type_different_int_param_verilog"))
    suite.addTest(unittest.makeSuite(HierarchySerializationTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
