#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from hwt.hdlObjects.types.union import HUnion
from hwtLib.types.ctypes import uint8_t, uint16_t, int8_t
from hwt.bitmask import mask
from hwt.hdlObjects.types.struct import HStruct


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
        v = t.fromPy(None)
        
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

        v = t.fromPy(None)
        
        v.struct.upper = 1
        self.assertEqual(v.bits.val, 1 << 8)
        self.assertEqual(v.bits.vldMask, mask(8) << 8)
        
        v.struct.lower = 1
        self.assertEqual(v.bits.val, (1 << 8) | 1)
        self.assertEqual(v.bits.vldMask, mask(16))
        
        v.bits = 2

        self.assertEqual(int(v.struct.lower), 2)
        self.assertEqual(int(v.struct.upper), 0)



if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(ValueTC('testValue'))
    suite.addTest(unittest.makeSuite(UnionTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
