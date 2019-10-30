#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
import unittest

from hwt.hdl.typeShortcuts import hBool, hInt, vec, hStr
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import INT


class ValueTC(unittest.TestCase):

    def assertValEq(self, first, second, msg=None):
        try:
            first = int(first)
        except ValueError:
            first = None

        return self.assertEqual(first, second, msg=msg)

    def assertValNEq(self, first, second, msg=None):
        return self.assertNotEqual(first.val, second, msg=msg)

    def test_value(self):
        self.assertTrue(vec(1, 1)._eq(vec(1, 1)))
        self.assertTrue(vec(0, 1)._eq(vec(0, 1)))
        self.assertTrue(vec(0, 2)._eq(vec(0, 2)))
        self.assertTrue(hBool(True)._eq(hBool(True)))
        v0 = vec(2, 2)
        v1 = v0.__copy__()
        self.assertTrue(v0._eq(v1))
        self.assertTrue(v0._eq(v1))

    def test_BOOLNeg(self):
        v0 = hBool(True)
        self.assertValEq(~v0, False)
        self.assertValEq(~ ~v0, True)

    def test_StringEq(self):
        v0 = hStr("abcd")
        v1 = hStr("abcd")
        v2 = hStr("sdff")
        v3 = hStr("asdfsadfsa")

        self.assertValEq(v0._eq(v1), True)
        self.assertValEq(v0._eq(v2), False)
        self.assertValEq(v0._eq(v3), False)

    def test_BoolEqualNotEqual(self):
        v0 = hBool(True)
        v1 = hBool(True)
        self.assertValEq(v0._eq(v1), True)
        self.assertNotEqual(v0, hBool(False))

    def test_BoolAnd(self):
        for a_in, b_in, out in [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)]:
            v0 = hBool(a_in)
            v1 = hBool(b_in)
            o = v0 & v1
            self.assertValEq(o, out, "%d == %d" % (o.val, out))

    def test_AddInt(self):
        v0 = hInt(0)
        v1 = hInt(1)
        v5 = hInt(5)

        self.assertValEq(v0 + v1, 1)
        self.assertValEq(v1 + v5, 6)
        self.assertValEq(v0 + v1 + v5, 6)

        self.assertValEq(v1 + hInt(1), 2)

    def test_DivInt(self):
        v8 = hInt(8)
        v4 = hInt(4)
        v2 = hInt(2)

        self.assertValEq(v8 // v4, 2)
        self.assertValEq(v8 // v2, 4)
        self.assertValEq(v4 // v2, 2)

    def test_BitsFromPyEnum(self):
        class PyEnumCls(Enum):
            A = 1
            B = 3
            C = 4

        t = Bits(2)

        self.assertValEq(t.from_py(PyEnumCls.A), 1)
        self.assertValEq(t.from_py(PyEnumCls.B), 3)
        with self.assertRaises(ValueError):
            t.from_py(PyEnumCls.C)

    def test_BitsFromIncompatibleType(self):
        t = Bits(2)
        with self.assertRaises(ValueError):
            t.from_py("a1")

        with self.assertRaises(TypeError):
            t.from_py(object())

    def test_Bits_int_autocast(self):
        uint2_t = Bits(2)
        v0 = INT.from_py(3)
        v1 = v0._auto_cast(uint2_t)
        self.assertEqual(v1._dtype, uint2_t)

        v2 = INT.from_py(10)
        with self.assertRaises(ValueError):
            v2._auto_cast(uint2_t)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(ValueTC('testValue'))
    suite.addTest(unittest.makeSuite(ValueTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
