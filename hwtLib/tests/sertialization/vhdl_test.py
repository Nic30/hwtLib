#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat
from hwt.hdl.typeShortcuts import hBit, vec
from hwt.interfaces.std import VectSignal
from hwt.synthesizer.unit import Unit
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.peripheral.spi.master import SpiMaster
from hwtLib.tests.sertialization.assignToCastAndSlices import AssignToASlice0, \
    AssignToASlice1, AssignToASlice2, AssignToASliceOfReg0, \
    AssignToASliceOfReg1a, AssignToASliceOfReg1b, AssignToASliceOfReg2a, AssignToASliceOfReg2b


class TernaryInConcatExample(Unit):

    def _declr(self):
        self.a = VectSignal(32)
        self.b = VectSignal(32)
        self.c = VectSignal(32)._m()

    def _impl(self):
        a = self.a
        b = self.b
        self.c(
            Concat(
                hBit(1),
                vec(7, 3),
                a != b,
                a < b,
                a <= b,
                a._eq(b),
                a >= b,
                a > b,
                vec(0, 22),
                )
            )


class Vhdl2008Serializer_TC(BaseSerializationTC):
    __FILE__ = __file__

    def test_add_to_slice_vhdl(self):
        u = TernaryInConcatExample()
        self.assert_serializes_as_file(u, "TernaryInConcatExample.vhd")

    def test_SpiMaster_vhdl(self):
        u = SpiMaster()
        self.assert_serializes_as_file(u, "SpiMaster.vhd")

    def test_AssignToASlice0(self):
        u = AssignToASlice0()
        self.assert_serializes_as_file(u, "AssignToASlice0.vhd")

    def test_AssignToASlice1(self):
        u = AssignToASlice1()
        self.assert_serializes_as_file(u, "AssignToASlice1.vhd")

    def test_AssignToASlice2(self):
        u = AssignToASlice2()
        self.assert_serializes_as_file(u, "AssignToASlice2.vhd")

    def test_AssignToASliceOfReg0(self):
        u = AssignToASliceOfReg0()
        self.assert_serializes_as_file(u, "AssignToASliceOfReg0.vhd")

    def test_AssignToASliceOfReg1a(self):
        u = AssignToASliceOfReg1a()
        self.assert_serializes_as_file(u, "AssignToASliceOfReg1a.vhd")

    def test_AssignToASliceOfReg1b(self):
        u = AssignToASliceOfReg1b()
        self.assert_serializes_as_file(u, "AssignToASliceOfReg1b.vhd")

    def test_AssignToASliceOfReg2a(self):
        u = AssignToASliceOfReg2a()
        self.assert_serializes_as_file(u, "AssignToASliceOfReg2a.vhd")

    def test_AssignToASliceOfReg2b(self):
        u = AssignToASliceOfReg2b()
        self.assert_serializes_as_file(u, "AssignToASliceOfReg2b.vhd")


if __name__ == '__main__':
    import unittest
    # from hwt.synthesizer.utils import to_rtl_str
    # print(to_rtl_str(TernaryInConcatExample()))
    suite = unittest.TestSuite()
    # suite.addTest(RdSyncedPipe('test_basic_data_pass'))
    suite.addTest(unittest.makeSuite(Vhdl2008Serializer_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
