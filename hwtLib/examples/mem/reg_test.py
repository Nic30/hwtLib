#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceLatch
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.rtlLevel.exceptions import SignalDriverErr
from hwt.synth import to_rtl_str, synthesised
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.mem.reg import DReg, DoubleDReg, OptimizedOutReg, \
    AsyncResetReg, DDR_Reg, LatchReg, DReg_asyncRst, RegWhereNextIsOnlyOutput
from hwtSimApi.constants import CLK_PERIOD


class DRegTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = DReg()
        cls.compileSim(cls.dut)

    def test_simple(self):
        self.dut.din._ag.data.extend(
            [i % 2 for i in range(6)] + [None, None, 0, 1])
        expected = [0, 0, 1, 0, 1, 0, 1, None, None, 0]

        self.runSim(11 * CLK_PERIOD)
        received = self.dut.dout._ag.data

        # check simulation results
        self.assertValSequenceEqual(received, expected)


class DoubleRRegTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = DoubleDReg()
        cls.compileSim(cls.dut)

    def test_double(self):
        self.dut.din._ag.data.extend(
            [i % 2 for i in range(6)] + [None, None, 0, 1])
        expected = [0, 0, 0, 1, 0, 1, 0, 1, None]

        self.runSim(10 * CLK_PERIOD)

        received = self.dut.dout._ag.data

        # check simulation results
        self.assertValSequenceEqual(received, expected)


class DReg_asyncRstTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = DReg_asyncRst()
        cls.compileSim(cls.dut)

    def test_async_rst(self):
        self.dut.rst._ag.initDelay = 3 * CLK_PERIOD
        self.dut.din._ag.data.extend([1, 0, 1, 0, 1])
        self.runSim(10 * CLK_PERIOD)
        self.assertValSequenceEqual(self.dut.dout._ag.data,
                                    [0, 1, 0, 1, 0, 1, 1])


class RegSerializationTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_optimizedOutReg(self):
        m = OptimizedOutReg()
        self.assertNotIn("unconnected", to_rtl_str(m))

    def test_regWhereNextIsOnlyOutput(self):
        m = RegWhereNextIsOnlyOutput()
        with self.assertRaises(SignalDriverErr):
            to_rtl_str(m)

    def test_dreg_vhdl(self):
        self.assert_serializes_as_file(DReg(), "DReg.vhd")

    def test_dreg_verilog(self):
        self.assert_serializes_as_file(DReg(), "DReg.v")

    def test_dreg_systemc(self):
        self.assert_serializes_as_file(DReg(), "DReg.cpp")

    def test_AsyncResetReg_vhdl(self):
        self.assert_serializes_as_file(AsyncResetReg(), "AsyncResetReg.vhd")

    def test_AsyncResetReg_verilog(self):
        self.assert_serializes_as_file(AsyncResetReg(), "AsyncResetReg.v")

    def test_DDR_Reg_vhdl(self):
        self.assert_serializes_as_file(DDR_Reg(), "DDR_Reg.vhd")

    def test_DDR_Reg_verilog(self):
        self.assert_serializes_as_file(DDR_Reg(), "DDR_Reg.v")

    def test_LatchReg_resources(self):
        m = LatchReg()
        expected = {
            ResourceLatch: 1,
        }

        s = ResourceAnalyzer()
        synthesised(m)
        s.visit_HwModule(m)
        self.assertDictEqual(s.report(), expected)


if __name__ == "__main__":
    import unittest
    _ALL_TCs = [DRegTC, DoubleRRegTC, DReg_asyncRstTC, RegSerializationTC]
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([DRegTC("test_dreg_systemc")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
