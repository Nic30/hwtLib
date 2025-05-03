#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.tests.serialization.hBitsMul import ExampleHBitsMul0a, \
    ExampleHBitsMul0b, ExampleHBitsMul1a, ExampleHBitsMul1b, ExampleHBitsMulS1a, \
    ExampleHBitsMulS1b, ExampleHBitsMul1c
from hwtLib.types.ctypes import uint8_t


class ExampleRom(HwModule):

    @override
    def hwDeclr(self):
        self.idx = HwIOSignal(HBits(2))
        self.data = HwIOSignal(HBits(8, signed=False))._m()

    @override
    def hwImpl(self):
        rom = self._sig(name="rom", dtype=uint8_t[4],
                                    def_val=[3, 10, 12, 99])

        self.data(rom[self.idx])


class VerilogSerializer_TC(BaseSerializationTC):
    __FILE__ = __file__

    def test_ExampleRom(self):
        m = ExampleRom()
        self.assert_serializes_as_file(m, "ExampleRom.v")

    def test_ExampleHBitsMul0a(self):
        m = ExampleHBitsMul0a()
        self.assert_serializes_as_file(m, "ExampleHBitsMul0a.v")

    def test_ExampleHBitsMul0b(self):
        m = ExampleHBitsMul0b()
        self.assert_serializes_as_file(m, "ExampleHBitsMul0b.v")

    def test_ExampleHBitsMul1a(self):
        m = ExampleHBitsMul1a()
        self.assert_serializes_as_file(m, "ExampleHBitsMul1a.v")

    def test_ExampleHBitsMul1b(self):
        m = ExampleHBitsMul1b()
        self.assert_serializes_as_file(m, "ExampleHBitsMul1b.v")

    def test_ExampleHBitsMul1c(self):
        m = ExampleHBitsMul1c()
        self.assert_serializes_as_file(m, "ExampleHBitsMul1c.v")

    def test_ExampleHBitsMulS1a(self):
        m = ExampleHBitsMulS1a()
        self.assert_serializes_as_file(m, "ExampleHBitsMulS1a.v")

    def test_ExampleHBitsMulS1b(self):
        m = ExampleHBitsMulS1b()
        self.assert_serializes_as_file(m, "ExampleHBitsMulS1b.v")




if __name__ == '__main__':
    import unittest
    # from hwt.synth import to_rtl_str
    # from hwt.serializer.verilog import VerilogSerializer
    # print(to_rtl_str(ExampleRom(), VerilogSerializer))
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([VerilogSerializer_TC("test_ExampleHBitsMul1c")])
    suite = testLoader.loadTestsFromTestCase(VerilogSerializer_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
