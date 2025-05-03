#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import BIT
from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.peripheral.spi.master import SpiMaster
from hwtLib.tests.serialization.assignToCastAndSlices import AssignToASlice0, \
    AssignToASlice1, AssignToASlice2, AssignToASliceOfReg0, \
    AssignToASliceOfReg1a, AssignToASliceOfReg1b, AssignToASliceOfReg2a, AssignToASliceOfReg2b, \
    AssignToASliceOfReg3a, AssignToASliceOfReg3b, AssignToASliceOfReg3c, \
    AssignToASliceOfReg3d
from hwtLib.tests.serialization.hBitsMul import ExampleHBitsMul0a, \
    ExampleHBitsMul0b, ExampleHBitsMul1a, ExampleHBitsMul1b, ExampleHBitsMulS1a, \
    ExampleHBitsMulS1b, ExampleHBitsMul1c


class TernaryInConcatExample(HwModule):

    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(32)
        self.b = HwIOVectSignal(32)
        self.c = HwIOVectSignal(32)._m()

    @override
    def hwImpl(self):
        a = self.a
        b = self.b
        self.c(
            Concat(
                BIT.from_py(1),
                HBits(3).from_py(7),
                a != b,
                a < b,
                a <= b,
                a._eq(b),
                a >= b,
                a > b,
                HBits(22).from_py(0),
                )
            )


class Vhdl2008Serializer_TC(BaseSerializationTC):
    __FILE__ = __file__

    def test_TernaryInConcatExample_vhdl(self):
        m = TernaryInConcatExample()
        self.assert_serializes_as_file(m, "TernaryInConcatExample.vhd")

    def test_SpiMaster_vhdl(self):
        m = SpiMaster()
        self.assert_serializes_as_file(m, "SpiMaster.vhd")

    def test_AssignToASlice0(self):
        m = AssignToASlice0()
        self.assert_serializes_as_file(m, "AssignToASlice0.vhd")

    def test_AssignToASlice1(self):
        m = AssignToASlice1()
        self.assert_serializes_as_file(m, "AssignToASlice1.vhd")

    def test_AssignToASlice2(self):
        m = AssignToASlice2()
        self.assert_serializes_as_file(m, "AssignToASlice2.vhd")

    def test_AssignToASliceOfReg0(self):
        m = AssignToASliceOfReg0()
        self.assert_serializes_as_file(m, "AssignToASliceOfReg0.vhd")

    def test_AssignToASliceOfReg1a(self):
        m = AssignToASliceOfReg1a()
        self.assert_serializes_as_file(m, "AssignToASliceOfReg1a.vhd")

    def test_AssignToASliceOfReg1b(self):
        m = AssignToASliceOfReg1b()
        self.assert_serializes_as_file(m, "AssignToASliceOfReg1b.vhd")

    def test_AssignToASliceOfReg2a(self):
        m = AssignToASliceOfReg2a()
        self.assert_serializes_as_file(m, "AssignToASliceOfReg2a.vhd")

    def test_AssignToASliceOfReg2b(self):
        m = AssignToASliceOfReg2b()
        self.assert_serializes_as_file(m, "AssignToASliceOfReg2b.vhd")

    def test_AssignToASliceOfReg3a(self):
        m = AssignToASliceOfReg3a()
        self.assert_serializes_as_file(m, "AssignToASliceOfReg3a.vhd")

    def test_AssignToASliceOfReg3b(self):
        m = AssignToASliceOfReg3b()
        self.assert_serializes_as_file(m, "AssignToASliceOfReg3b.vhd")

    def test_AssignToASliceOfReg3c(self):
        m = AssignToASliceOfReg3c()
        self.assert_serializes_as_file(m, "AssignToASliceOfReg3c.vhd")

    def test_AssignToASliceOfReg3d(self):
        m = AssignToASliceOfReg3d()
        self.assert_serializes_as_file(m, "AssignToASliceOfReg3d.vhd")

    def test_ExampleHBitsMul0a(self):
        m = ExampleHBitsMul0a()
        self.assert_serializes_as_file(m, "ExampleHBitsMul0a.vhd")

    def test_ExampleHBitsMul0b(self):
        m = ExampleHBitsMul0b()
        self.assert_serializes_as_file(m, "ExampleHBitsMul0b.vhd")

    def test_ExampleHBitsMul1a(self):
        m = ExampleHBitsMul1a()
        self.assert_serializes_as_file(m, "ExampleHBitsMul1a.vhd")

    def test_ExampleHBitsMul1b(self):
        m = ExampleHBitsMul1b()
        self.assert_serializes_as_file(m, "ExampleHBitsMul1b.vhd")

    def test_ExampleHBitsMul1c(self):
        m = ExampleHBitsMul1c()
        self.assert_serializes_as_file(m, "ExampleHBitsMul1c.vhd")

    def test_ExampleHBitsMulS1a(self):
        m = ExampleHBitsMulS1a()
        self.assert_serializes_as_file(m, "ExampleHBitsMulS1a.vhd")

    def test_ExampleHBitsMulS1b(self):
        m = ExampleHBitsMulS1b()
        self.assert_serializes_as_file(m, "ExampleHBitsMulS1b.vhd")


if __name__ == '__main__':
    import unittest
    # from hwt.synth import to_rtl_str
    # print(to_rtl_str(TernaryInConcatExample()))
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Vhdl2008Serializer_TC("test_AssignToASlice0")])
    suite = testLoader.loadTestsFromTestCase(Vhdl2008Serializer_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
