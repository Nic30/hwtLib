#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import BIT, BOOL
from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal
from hwt.hwIOs.utils import addClkRstn
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


class Assign1bVec(HwModule):

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.i0 = HwIOSignal(HBits(1))
        self.i1v = HwIOSignal(HBits(1, force_vector=True))

        self.o0 = HwIOSignal(HBits(1))._m()
        self.o1v = HwIOSignal(HBits(1, force_vector=True))._m()

        self.o2 = HwIOSignal(HBits(1))._m()
        self.o3v = HwIOSignal(HBits(1, force_vector=True))._m()

    @override
    def hwImpl(self):
        self.o0(self.i0)
        self.o1v(self.i0)

        self.o2(self.i1v)
        self.o3v(self.i1v)


class Assign1bVecWithCast(HwModule):

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.i0 = HwIOSignal(HBits(1))
        self.i1v = HwIOSignal(HBits(1, force_vector=True))

        self.o0 = HwIOSignal(HBits(1))._m()
        self.o1v = HwIOSignal(HBits(1, force_vector=True))._m()

        self.o2 = HwIOSignal(HBits(1))._m()
        self.o3v = HwIOSignal(HBits(1, force_vector=True))._m()

    @override
    def hwImpl(self):
        i0asV = self.i0._reinterpret_cast(HBits(1, force_vector=True))
        self.o0(i0asV)
        self.o1v(i0asV)

        i0vAsBit = self.i1v._reinterpret_cast(HBits(1, force_vector=False))
        self.o2(i0vAsBit)
        self.o3v(i0vAsBit)


class Assign1bVecBool(HwModule):

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.i0 = HwIOSignal(HBits(1))
        self.i1v = HwIOSignal(HBits(1, force_vector=True))
        self.i2bool = HwIOSignal(BOOL)

        self.o0 = HwIOSignal(HBits(1))._m()
        self.o1v = HwIOSignal(HBits(1, force_vector=True))._m()
        self.o2bool = HwIOSignal(BOOL)._m()
        self.o3bool = HwIOSignal(BOOL)._m()
        self.o4bool = HwIOSignal(BOOL)._m()

    @override
    def hwImpl(self):
        self.o0(self.i2bool)
        self.o1v(self.i2bool)

        self.o2bool(self.i0)
        self.o3bool(self.i1v)
        self.o4bool(self.i2bool)


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

    def test_Assign1bVec(self):
        m = Assign1bVec()
        self.assert_serializes_as_file(m, "Assign1bVec.vhd")

    def test_Assign1bVecWithCast(self):
        m = Assign1bVec()
        self.assert_serializes_as_file(m, "Assign1bVecWithCast.vhd")

    def test_Assign1bVecBool(self):
        m = Assign1bVec()
        self.assert_serializes_as_file(m, "Assign1bVecBool.vhd")


if __name__ == '__main__':
    import unittest
    # from hwt.synth import to_rtl_str
    # print(to_rtl_str(Assign1bVecBool()))
    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(Vhdl2008Serializer_TC)
    # suite = unittest.TestSuite([Vhdl2008Serializer_TC("test_AssignToASliceOfReg1b")])
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
