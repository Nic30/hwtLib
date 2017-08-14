#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.typeShortcuts import hBool, hInt, vec, hStr
from enum import Enum
from hwt.hdlObjects.types.bits import Bits
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.hdlObjects.types.defs import BIT


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
        v1 = v0.clone()
        self.assertTrue(v0._eq(v1))
        v1.updateTime = 2
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

        self.assertValEq(t.fromPy(PyEnumCls.A), 1)
        self.assertValEq(t.fromPy(PyEnumCls.B), 3)
        with self.assertRaises(ValueError):
            t.fromPy(PyEnumCls.C)

    def test_BitsFromIncompatibleType(self):
        t = Bits(2)
        with self.assertRaises(ValueError):
            t.fromPy("a1")

        with self.assertRaises(TypeError):
            t.fromPy(object())

    def test_BitsIndexOnSingleBit(self):
        t = Bits(1)
        v = t.fromPy(1)
        with self.assertRaises(TypeError):
            v[0]

        t = Bits(1, forceVector=True)
        v = t.fromPy(1)
        self.assertValEq(v[0], 1)

    def test_BitsConcatIncompatibleType(self):
        t = Bits(1)
        v = t.fromPy(1)
        with self.assertRaises(TypeError):
            v._concat(hInt(2))
        p = Param(1)
        with self.assertRaises(TypeError):
            v._concat(p)

    def test_BitsIndexTypes(self):
        t = Bits(8)
        v = t.fromPy(1)
        with self.assertRaises(TypeError):
            v[object()]
        with self.assertRaises(IndexError):
            v[9:]
        with self.assertRaises(IndexError):
            v[:-1]

        p = Param(2)
        self.assertIsInstance(v[p], RtlSignalBase)
        self.assertEqual(v[p]._dtype.bit_length(), 1)

        p2 = p._downto(0)
        self.assertIsInstance(v[p2], RtlSignalBase)
        self.assertEqual(v[p2]._dtype.bit_length(), 2)

        p3 = Param("abc")
        with self.assertRaises(TypeError):
            v[p3]

        a = RtlSignal(None, "a", BIT)
        a._const = False
        with self.assertRaises(TypeError):
            v[p] = a

        with self.assertRaises(TypeError):
            v[a] = p

        v[p] = 1
        self.assertValEq(v, 5)

        v[p2] = 2
        self.assertValEq(v, 6)

        with self.assertRaises(TypeError):
            v[hInt(None)] = 2

        v[:] = 0
        self.assertValEq(v, 0)

        v[2] = 1
        self.assertValEq(v, 4)
        v[3:] = p
        self.assertValEq(v, 2)

        v._setitem__val(hInt(None), hInt(1))
        self.assertValEq(v, None)

        with self.assertRaises(TypeError):
            v[hStr("asfs")]

    def test_BitsMulInvalidType(self):
        t = Bits(8)
        v = t.fromPy(1)
        with self.assertRaises(TypeError):
            v * "a"


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(ValueTC('testValue'))
    suite.addTest(unittest.makeSuite(ValueTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
