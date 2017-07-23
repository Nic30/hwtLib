#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.serializer.systemC.serializer import SystemCSerializer
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.shortcuts import toRtl
from hwtLib.samples.hierarchy.groupOfBlockrams import GroupOfBlockrams, \
    groupOfBlockrams_as_vhdl
from hwtLib.samples.hierarchy.netFilter import NetFilter
from hwtLib.samples.hierarchy.netFilter_serialized import netFilter_vhdl, \
    netFilter_verilog, netFilter_systemc
from hwtLib.tests.statementTrees import StatementTreesTC


class HierarchySerializationTC(SimTestCase):

    def test_NetFilter_vhdl(self):
        u = NetFilter()
        s = toRtl(u, serializer=VhdlSerializer)
        StatementTreesTC.strStructureCmp(self, s, netFilter_vhdl)

    def test_NetFilter_verilog(self):
        u = NetFilter()
        s = toRtl(u, serializer=VerilogSerializer)
        StatementTreesTC.strStructureCmp(self, s, netFilter_verilog)

    def test_NetFilter_systemc(self):
        u = NetFilter()
        s = toRtl(u, serializer=SystemCSerializer)
        StatementTreesTC.strStructureCmp(self, s, netFilter_systemc)

    def test_groupOfBlockrams_vhdl(self):
        u = GroupOfBlockrams()
        s = toRtl(u, serializer=VhdlSerializer)
        StatementTreesTC.strStructureCmp(self, s, groupOfBlockrams_as_vhdl)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HierarchySerializationTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
