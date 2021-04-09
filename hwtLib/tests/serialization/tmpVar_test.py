#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import VectSignal
from hwt.synthesizer.unit import Unit
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwt.code import Concat, If


class TmpVarExample0(Unit):

    def _declr(self):
        self.a = VectSignal(32)
        self.b = VectSignal(32)._m()

    def _impl(self):
        a = self.a[8:] + 4
        self.b(a[4:], fit=True)


class TmpVarExample1(Unit):

    def _declr(self):
        self.a = VectSignal(32)
        self.b = VectSignal(32)._m()

    def _impl(self):
        a = self.a
        c = Concat(a[:16]._eq(1), a[16:]._eq(1))
        b = self.b
        If(c[0]._eq(0) & c[1]._eq(0),
           b(0)
        ).Else(
           b(1)
        )


class TmpVarExample2(Unit):

    def _declr(self):
        self.a = VectSignal(32)
        self.b = VectSignal(32)._m()

    def _impl(self):
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


if __name__ == '__main__':
    import unittest

    suite = unittest.TestSuite()
    # suite.addTest(RdSyncedPipe('test_basic_data_pass'))
    suite.addTest(unittest.makeSuite(Serializer_tmpVar_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
