#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.union import HUnion
from hwtLib.types.ctypes import uint8_t, uint16_t, int8_t, uint32_t
from pyMathBitPrecise.bit_utils import mask


class UnionTC(unittest.TestCase):
    def test_assertMembersSameSize(self):
        t = HUnion(
            (uint8_t, "a"),
            (uint8_t, "b"),
            (uint8_t, "c"),
            (uint8_t, "d"),
            )
        self.assertEqual(t.bit_length(), 8)

        with self.assertRaises(TypeError):
            HUnion(
                (uint16_t, "a"),
                (uint8_t, "b"),
            )

    def test_assertNoPadding(self):
        with self.assertRaises(AssertionError):
            HUnion(
                (uint8_t, None),
                (uint8_t, "b"),
            )

    def test_value_simple(self):
        t = HUnion(
                (uint8_t, "unsigned"),
                (int8_t, "signed"),
            )
        v = t.from_py(None)

        v.unsigned = mask(8)
        self.assertEqual(int(v.signed), -1)

        v.signed = 0
        self.assertEqual(int(v.unsigned), 0)

    def test_value_struct_and_bits(self):
        t = HUnion(
                (uint16_t, "bits"),
                (HStruct(
                  (uint8_t, "lower"),
                  (uint8_t, "upper"),
                 ), "struct"),
            )

        v = t.from_py(None)

        v.struct.upper = 1
        self.assertEqual(v.bits.val, 1 << 8)
        self.assertEqual(v.bits.vld_mask, mask(8) << 8)

        v.struct.lower = 1
        self.assertEqual(v.bits.val, (1 << 8) | 1)
        self.assertEqual(v.bits.vld_mask, mask(16))

        v.bits = 2

        self.assertEqual(int(v.struct.lower), 2)
        self.assertEqual(int(v.struct.upper), 0)

    def test_value_array_and_bits(self):
        t = HUnion(
                (uint32_t, "bits"),
                (uint8_t[4], "arr"),
            )

        v = t.from_py(None)

        b = (4 << (3 * 8)) | (3 << (2 * 8)) | (2 << 8) | 1
        v.bits = b

        for i, item in enumerate(v.arr):
            self.assertEqual(int(item), i + 1)

        self.assertEqual(int(v.bits), b)

    def test_value_array_toArray(self):
        t = HUnion(
                (uint16_t[2], "arr16b"),
                (int8_t[4], "arr8b"),
            )

        v = t.from_py(None)

        for i in range(len(v.arr16b)):
            v.arr16b[i] = i + 1

        for i, item in enumerate(v.arr8b):
            if (i + 1) % 2 == 0:
                v = 0
            else:
                v = i // 2 + 1
            self.assertEqual(int(item), v)

    def test_value_array_of_struct_to_bits(self):
        t = HUnion(
                (HStruct(
                    (uint16_t, "a"),
                    (uint8_t, "b"),
                    )[3], "arr"),
                (Bits(24 * 3), "bits")
            )

        v = t.from_py(None)
        for i in range(len(v.arr)):
            v.arr[i] = {"a": i + 1,
                        "b": (i + 1) * 3
                        }

        self.assertEqual(int(v.bits),
                         1
                         | 3 << 16
                         | 2 << 24
                         | 6 << (24 + 16)
                         | 3 << (2 * 24)
                         | 9 << (2 * 24 + 16))

    def test_hunion_type_eq(self):
        t0 = HUnion(
                (HStruct(
                    (uint16_t, "a"),
                    (uint8_t, "b"),
                    )[3], "arr"),
                (Bits(24 * 3), "bits")
            )
        t1 = HUnion(
                (HStruct(
                    (uint16_t, "a"),
                    (uint8_t, "b"),
                    )[3], "arr"),
                (Bits(24 * 3), "bits")
            )
        self.assertEqual(t0, t1)
        self.assertEqual(t1, t0)

        t1 = HUnion(
                (Bits(24 * 3), "bits"),
                (HStruct(
                    (uint16_t, "a"),
                    (uint8_t, "b"),
                    )[3], "arr")
            )

        self.assertEqual(t0, t1)
        self.assertEqual(t1, t0)

        t1 = HUnion(
                (uint32_t, "bits"),
                (uint8_t[4], "arr"),
            )
        self.assertNotEqual(t0, t1)
        self.assertNotEqual(t1, t0)

        t1 = HUnion(
                (Bits(24 * 3), "bbits"),
                (HStruct(
                    (uint16_t, "a"),
                    (uint8_t, "b"),
                    )[3], "arr")
            )
        self.assertNotEqual(t0, t1)
        self.assertNotEqual(t1, t0)

        t1 = Bits(24 * 3)
        self.assertNotEqual(t0, t1)
        self.assertNotEqual(t1, t0)

        t1 = HUnion(
                (Bits(24 * 3, signed=False), "bits"),
                (HStruct(
                    (uint16_t, "a"),
                    (uint8_t, "b"),
                    )[3], "arr")
            )
        self.assertNotEqual(t0, t1)
        self.assertNotEqual(t1, t0)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(ValueTC('testValue'))
    suite.addTest(unittest.makeSuite(UnionTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
