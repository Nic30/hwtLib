#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat, If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwtLib.examples.base_serialization_TC import BaseSerializationTC


class TmpVarExample0(HwModule):

    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(32)
        self.b = HwIOVectSignal(32)._m()

    @override
    def hwImpl(self):
        a = self.a[8:] + 4
        self.b(a[4:], fit=True)


class TmpVarExample1(HwModule):

    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(32)
        self.b = HwIOVectSignal(32)._m()

    @override
    def hwImpl(self):
        a = self.a
        c = Concat(a[:16]._eq(1), a[16:]._eq(1))
        b = self.b
        If(c[0]._eq(0) & c[1]._eq(0),
           b(0)
        ).Else(
           b(1)
        )


class TmpVarExample2(HwModule):

    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(32)
        self.b = HwIOVectSignal(32)._m()

    @override
    def hwImpl(self):
        a = self.a
        c = Concat(a[:16]._eq(1), a[16:]._eq(1))
        c = c + 1
        c = Concat(c[0], c[1])

        b = self.b
        If(c[0]._eq(0) & c[1]._eq(0),
           b(0)
        ).Else(
           b(1)
        )


class TmpVarExampleTernary(HwModule):

    @override
    def hwDeclr(self) -> None:
        self.a = HwIOSignal()
        self.b = HwIOVectSignal(1)
        self.c = HwIOSignal()

        self.d = HwIOVectSignal(1)._m()
        self.e = HwIOVectSignal(1)._m()
        self.f = HwIOSignal()._m()
        self.g = HwIOSignal()._m()

    @override
    def hwImpl(self) -> None:
        a = self.a
        b = self.b
        c = self.c
        self.d(c._ternary(a, b))
        self.e(c._ternary(b, a))
        self.f(c._ternary(a, b))
        self.g(c._ternary(b, a))


class TmpVarSignCast(HwModule):

    @override
    def hwDeclr(self) -> None:
        self.a = HwIOSignal()
        self.b = HwIOSignal(dtype=HBits(1, signed=False))
        self.c = HwIOSignal(dtype=HBits(1, signed=False))._m()
        self.d = HwIOSignal(dtype=HBits(1, signed=False))._m()

        self.e = HwIOVectSignal(2)
        self.i = HwIOSignal()
        self.o = HwIOSignal()._m()

    @override
    def hwImpl(self) -> None:
        self.c(self.a + self.b)
        self.d(self.b + self.a)
        self.o(self.e[self.i])


class Serializer_tmpVar_TC(BaseSerializationTC):
    __FILE__ = __file__

    def test_add_to_slice_vhdl(self):
        self.assert_serializes_as_file(TmpVarExample0(), "TmpVarExample0.vhd")

    def test_TmpVarExample1_vhdl(self):
        self.assert_serializes_as_file(TmpVarExample1(), "TmpVarExample1.vhd")

    def test_TmpVarExample1_verilog(self):
        self.assert_serializes_as_file(TmpVarExample1(), "TmpVarExample1.v")

    def test_TmpVarExample2_vhdl(self):
        self.assert_serializes_as_file(TmpVarExample2(), "TmpVarExample2.vhd")

    def test_TmpVarExample2_verilog(self):
        self.assert_serializes_as_file(TmpVarExample2(), "TmpVarExample2.v")

    def test_TmpVarExampleTernary_vhdl(self):
        self.assert_serializes_as_file(TmpVarExampleTernary(), "TmpVarExampleTernary.vhd")

    def test_TmpVarSignCast_vhdl(self):
        self.assert_serializes_as_file(TmpVarSignCast(), "TmpVarSignCast.vhd")


if __name__ == '__main__':
    import unittest

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Serializer_tmpVar_TC("test_TmpVarExample1_vhdl")])
    suite = testLoader.loadTestsFromTestCase(Serializer_tmpVar_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
