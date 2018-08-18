#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from hwt.serializer.systemC.serializer import SystemCSerializer
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.utils import toRtl

from hwtLib.samples.hierarchy.groupOfBlockrams import GroupOfBlockrams, \
    groupOfBlockrams_as_vhdl
from hwtLib.samples.hierarchy.netFilter import NetFilter
from hwtLib.tests.statementTrees import StatementTreesTC


def readContent(file_name:str):
    THIS_DIR = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(THIS_DIR, file_name)) as f:
        return f.read()


class HierarchySerializationTC(SimTestCase):

    def test_NetFilter_vhdl(self):
        u = NetFilter()
        s = toRtl(u, serializer=VhdlSerializer)
        netFilter_vhdl = readContent("netFilter.vhd")
        StatementTreesTC.strStructureCmp(self, s, netFilter_vhdl)

    def test_NetFilter_verilog(self):
        u = NetFilter()
        s = toRtl(u, serializer=VerilogSerializer)
        netFilter_verilog = readContent("netFilter.v")
        StatementTreesTC.strStructureCmp(self, s, netFilter_verilog)

    def test_NetFilter_systemc(self):
        u = NetFilter()
        s = toRtl(u, serializer=SystemCSerializer)
        netFilter_systemc = readContent("netFilter.cpp")
        StatementTreesTC.strStructureCmp(self, s, netFilter_systemc)

    def test_groupOfBlockrams_vhdl(self):
        u = GroupOfBlockrams()
        s = toRtl(u, serializer=VhdlSerializer)
        StatementTreesTC.strStructureCmp(self, s, groupOfBlockrams_as_vhdl)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HierarchySerializationTC("test_NetFilter_systemc"))
    suite.addTest(unittest.makeSuite(HierarchySerializationTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
