#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Signal
from hwt.interfaces.structIntf import HdlType_to_Interface
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit
from hwtLib.types.ctypes import uint8_t

example_struct_simple = HStruct(
    (uint8_t, "a0"),
)

example_struct2x = HStruct(
    (uint8_t, "a0"),
    (uint8_t, "a1"),
)

example_struct_nested = HStruct(
    (example_struct2x, "a0"),
    (uint8_t, "a1"),
)


class ExampleTCmp(Unit):

    def __init__(self, t: HdlType):
        self.t = t
        super(ExampleTCmp, self).__init__()

    def _declr(self):
        self.a = HdlType_to_Interface().apply(self.t)
        self.b = HdlType_to_Interface().apply(self.t)

        self.a_eq_b_out = Signal()._m()
        self.a_ne_b_out = Signal()._m()

    def _impl(self):
        a, b = self.a, self.b
        self.a_eq_b = a._eq(b)
        self.a_ne_b = a != b

        self.a_eq_b_out(self.a_eq_b)
        self.a_ne_b_out(self.a_ne_b)
        return a, b


class StructIntf_operatorTC(SimTestCase):

    def test_eq_simple(self):

        class _ExampleTCmp(ExampleTCmp):

            def _impl(self):
                a, b = super(_ExampleTCmp, self)._impl()
                assert self.a_eq_b is a.a0._eq(b.a0)
                assert self.a_ne_b is (a.a0 != b.a0), self.a_ne_b

        u = _ExampleTCmp(example_struct_simple)
        self.compileSim(u)

    def test_eq_simple2x(self):

        class _ExampleTCmp(ExampleTCmp):

            def _impl(self):
                a, b = super(_ExampleTCmp, self)._impl()
                assert self.a_eq_b is a.a0._eq(b.a0) & a.a1._eq(b.a1)
                assert self.a_ne_b is ((a.a0 != b.a0) | (a.a1 != b.a1)), self.a_ne_b

        u = _ExampleTCmp(example_struct2x)
        self.compileSim(u)

    def test_eq_simpleNested(self):

        class _ExampleTCmp(ExampleTCmp):

            def _impl(self):
                a, b = super(_ExampleTCmp, self)._impl()
                assert self.a_eq_b is a.a0._eq(b.a0) & a.a1._eq(b.a1)
                assert self.a_ne_b is ((a.a0.a0 != b.a0.a0) | (a.a0.a1 != b.a0.a1) | (a.a1 != b.a1)), self.a_ne_b

        u = _ExampleTCmp(example_struct_nested)
        self.compileSim(u)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(StructIntf_operatorTC('test_eq_simple'))
    suite.addTest(unittest.makeSuite(StructIntf_operatorTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
