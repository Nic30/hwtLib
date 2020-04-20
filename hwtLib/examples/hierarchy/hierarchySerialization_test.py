#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.hierarchy.groupOfBlockrams import GroupOfBlockrams
from hwtLib.examples.hierarchy.netFilter import NetFilter


class HierarchySerializationTC(BaseSerializationTC):

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


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HierarchySerializationTC("test_NetFilter_systemc"))
    suite.addTest(unittest.makeSuite(HierarchySerializationTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
