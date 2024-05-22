#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwtLib.examples.base_serialization_TC import BaseSerializationTC


class VhdlVectorAutoCastExample(HwModule):

    @override
    def hwDeclr(self):
        std_logic = HBits(1)
        std_logic_vector_0 = HBits(1, force_vector=True)

        self.a = HwIOSignal(dtype=std_logic)
        self.b = HwIOSignal(dtype=std_logic)._m()

        self.c = HwIOSignal(dtype=std_logic_vector_0)._m()

        self.d = HwIOSignal(dtype=std_logic_vector_0)
        self.e = HwIOSignal(dtype=std_logic)._m()

        self.f = HwIOSignal(dtype=std_logic)
        self.g = HwIOSignal(dtype=std_logic_vector_0)

        self.i = HwIOSignal(dtype=std_logic)._m()

        self.j = HwIOSignal(dtype=std_logic)._m()

    @override
    def hwImpl(self):
        # no conversion
        self.b(self.a)

        # std_logic -> std_logic_vector
        self.c(self.a)
        # std_logic_vector -> std_logic
        self.e(self.d)

        # unsigned(std_logic)  + unsigned(std_logic_vector) -> std_logic_vector ->  std_logic
        self.i(self.f + self.g)

        # unsigned(std_logic)  + unsigned(std_logic_vector) -> std_logic_vector ->  std_logic
        self.j(self.g + self.f)


class VhdlVectorAutoCastExampleTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_vhdl(self):
        m = VhdlVectorAutoCastExample()
        self.assert_serializes_as_file(m, "VhdlVectorAutoCastExample.vhd")


if __name__ == '__main__':
    from hwt.synth import to_rtl_str
    from hwt.serializer.vhdl import Vhdl2008Serializer

    m = VhdlVectorAutoCastExample()
    print(to_rtl_str(m, Vhdl2008Serializer))

    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([VhdlVectorAutoCastExampleTC("test_vhdl")])
    suite = testLoader.loadTestsFromTestCase(VhdlVectorAutoCastExampleTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
