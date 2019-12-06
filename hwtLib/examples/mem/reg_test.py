#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import unittest
from unittest.case import TestCase

from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceLatch
from hwt.serializer.systemC.serializer import SystemCSerializer
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.utils import toRtl
from hwtLib.examples.mem.reg import DReg, DoubleDReg, OptimizedOutReg, \
    AsyncResetReg, DDR_Reg, Latch, DReg_asyncRst
from pycocotb.constants import CLK_PERIOD


class DRegTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        return DReg()

    def test_simple(self):
        self.u.din._ag.data.extend(
            [i % 2 for i in range(6)] + [None, None, 0, 1])
        expected = [0, 0, 1, 0, 1, 0, 1, None, None, 0]

        self.runSim(11 * CLK_PERIOD)
        recieved = self.u.dout._ag.data

        # check simulation results
        self.assertValSequenceEqual(recieved, expected)


class DoubleRRegTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        return DoubleDReg()

    def test_double(self):
        self.u.din._ag.data.extend(
            [i % 2 for i in range(6)] + [None, None, 0, 1])
        expected = [0, 0, 0, 1, 0, 1, 0, 1, None]

        self.runSim(10 * CLK_PERIOD)

        recieved = self.u.dout._ag.data

        # check simulation results
        self.assertValSequenceEqual(recieved, expected)


class DReg_asyncRstTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        return DReg_asyncRst()

    def test_async_rst(self):
        self.u.rst._ag.initDelay = 3 * CLK_PERIOD
        self.u.din._ag.data.extend([1, 0, 1, 0, 1])
        self.runSim(10 * CLK_PERIOD)
        self.assertValSequenceEqual(self.u.dout._ag.data,
                                    [0, 1, 0, 1, 0, 1, 1])


class RegSerializationTC(TestCase):

    def assertEqualToFile(self, value, file_name):
        THIS_DIR = os.path.dirname(os.path.realpath(__file__))
        fn = os.path.join(THIS_DIR, file_name)
        # with open(fn, "w") as f:
        #     f.write(value)
        with open(fn) as f:
            file_content = f.read()
        self.assertEqual(value, file_content)

    def test_optimizedOutReg(self):
        u = OptimizedOutReg()
        self.assertNotIn("unconnected", toRtl(u))

    def test_dreg_vhdl(self):
        s = toRtl(DReg(), serializer=VhdlSerializer)
        self.assertEqualToFile(s, "DReg.vhd")

    def test_dreg_verilog(self):
        s = toRtl(DReg(), serializer=VerilogSerializer)
        self.assertEqualToFile(s, "DReg.v")

    def test_dreg_systemc(self):
        s = toRtl(DReg(), serializer=SystemCSerializer)
        self.assertEqualToFile(s, "DReg.cpp")

    def test_AsyncResetReg_vhdl(self):
        s = toRtl(AsyncResetReg(), serializer=VhdlSerializer)
        self.assertEqualToFile(s, "AsyncResetReg.vhd")

    def test_AsyncResetReg_verilog(self):
        s = toRtl(AsyncResetReg(), serializer=VerilogSerializer)
        self.assertEqualToFile(s, "AsyncResetReg.v")

    def test_DDR_Reg_vhdl(self):
        s = toRtl(DDR_Reg(), serializer=VhdlSerializer)
        self.assertEqualToFile(s, "DDR_Reg.vhd")

    def test_DDR_Reg_verilog(self):
        s = toRtl(DDR_Reg(), serializer=VerilogSerializer)
        self.assertEqualToFile(s, "DDR_Reg.v")

    def test_latch_resources(self):
        u = Latch()
        expected = {
            ResourceLatch: 1,
        }

        s = ResourceAnalyzer()
        toRtl(u, serializer=s)
        self.assertDictEqual(s.report(), expected)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(DRegTC('test_optimizedOutReg'))
    suite.addTest(unittest.makeSuite(DRegTC))
    suite.addTest(unittest.makeSuite(DoubleRRegTC))
    suite.addTest(unittest.makeSuite(DReg_asyncRstTC))
    suite.addTest(unittest.makeSuite(RegSerializationTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
