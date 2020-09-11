#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.hierarchy.groupOfBlockrams import GroupOfBlockrams
from hwtLib.examples.hierarchy.netFilter import NetFilter
from hwtLib.examples.hierarchy.rippleadder import RippleAdder0, \
    RippleAdder1, RippleAdder2, RippleAdder3


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


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HierarchySerializationTC("test_NetFilter_systemc"))
    suite.addTest(unittest.makeSuite(HierarchySerializationTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
