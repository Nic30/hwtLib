#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from hwt.hdlObjects.types.union import HUnion
from hwtLib.types.ctypes import uint8_t, uint16_t


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


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(ValueTC('testValue'))
    suite.addTest(unittest.makeSuite(UnionTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
