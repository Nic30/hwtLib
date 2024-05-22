#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
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

    def test_add_to_slice_vhdl(self):
        m = ExampleRom()
        self.assert_serializes_as_file(m, "ExampleRom.v")


if __name__ == '__main__':
    import unittest
    from hwt.synth import to_rtl_str
    from hwt.serializer.verilog import VerilogSerializer
    print(to_rtl_str(ExampleRom(), VerilogSerializer))
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Verilog2005Serializer_TC("test_basic_data_pass")])
    suite = testLoader.loadTestsFromTestCase(VerilogSerializer_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
