#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from unittest.case import TestCase

from hwt.serializer.systemC.serializer import SystemCSerializer
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.utils import toRtl
from hwtLib.examples.hierarchy.groupOfBlockrams import GroupOfBlockrams
from hwtLib.examples.hierarchy.netFilter import NetFilter
from hwtLib.tests.statementTrees import StatementTreesTC


class HierarchySerializationTC(TestCase):

    def assert_same_as_file(self, s, file_name: str):
        THIS_DIR = os.path.dirname(os.path.realpath(__file__))
        fn = os.path.join(THIS_DIR, file_name)
        # with open(fn, "w") as f:
        #     f.write(s)
        with open(fn) as f:
            ref_s = f.read()
        StatementTreesTC.strStructureCmp(self, s, ref_s)

    def test_NetFilter_vhdl(self):
        u = NetFilter()
        s = toRtl(u, serializer=VhdlSerializer)
        self.assert_same_as_file(s, "netFilter.vhd")

    def test_NetFilter_verilog(self):
        u = NetFilter()
        s = toRtl(u, serializer=VerilogSerializer)
        self.assert_same_as_file(s, "netFilter.v")

    def test_NetFilter_systemc(self):
        u = NetFilter()
        s = toRtl(u, serializer=SystemCSerializer)
        self.assert_same_as_file(s, "netFilter.cpp")

    def test_groupOfBlockrams_vhdl(self):
        u = GroupOfBlockrams()
        s = toRtl(u, serializer=VhdlSerializer)
        self.assert_same_as_file(s, "GroupOfBlockrams.vhd")


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HierarchySerializationTC("test_NetFilter_systemc"))
    suite.addTest(unittest.makeSuite(HierarchySerializationTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
