#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.shortcuts import toRtl
from hwtLib.samples.hierarchy.netFilter import NetFilter
from hwtLib.samples.hierarchy.netFilter_serialized import netFilter_vhdl, \
    netFilter_verilog, netFilter_systemc
from hwtLib.tests.statementTrees import StatementTreesTC
from hwt.serializer.systemC.serializer import SystemCSerializer


class NetFilterTC(SimTestCase):

    def test_vhdl_serialization(self):
        u = NetFilter()
        s = toRtl(u, serializer=VhdlSerializer)
        StatementTreesTC.strStructureCmp(self, s, netFilter_vhdl)
        # print(toRtl(u))

    def test_verilog_serialization(self):
        u = NetFilter()
        s = toRtl(u, serializer=VerilogSerializer)
        StatementTreesTC.strStructureCmp(self, s, netFilter_verilog)

    def test_systemc_serialization(self):
        u = NetFilter()
        s = toRtl(u, serializer=SystemCSerializer)
        StatementTreesTC.strStructureCmp(self, s, netFilter_systemc)

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NetFilterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)