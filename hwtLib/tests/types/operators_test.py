#!/usr/bin/env python3alu
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.typeShortcuts import hInt, hBool, hBit, vec
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import INT, STR, BOOL
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from pyMathBitPrecise.bit_utils import mask
from hwt.hdl.operatorDefs import downtoFn, toFn


n = RtlNetlist()
s0 = n.sig("s0", BOOL)
s1 = n.sig("s1")

andTable = [(None, None, None),
            (None, 0, 0),
            (None, 1, None),
            (0, None, 0),
            (0, 0, 0),
            (0, 1, 0),
            (1, 1, 1),
            (s0, 1, s0),
            (s0, 0, 0),
            (1, s0, s0),
            (0, s0, 0),
            ]
orTable = [(None, None, None),
           (None, 0, None),
           (None, 1, 1),
           (0, None, None),
           (0, 0, 0),
           (0, 1, 1),
           (1, 1, 1),
           (s0, 1, 1),
           (s0, 0, s0),
           (1, s0, 1),
           (0, s0, s0),
           ]
xorTable = [(None, None, None),
            (None, 0, None),
            (None, 1, None),
            (0, None, None),
            (0, 0, 0),
            (0, 1, 1),
            (1, 1, 0),
            (s0, 1, ~s0),
            (s0, 0, s0),
            (1, s0, ~s0),
            (0, s0, s0),
            ]

bitvals = {
    1: hBit(1),
    0: hBit(0),
    None: hBit(None),
    s0: s1,
    ~ s0: ~s1
}

boolvals = {
    1: hBool(1),
    0: hBool(0),
    None: hBool(None),
    s0: s0,
    ~ s0: ~s0
}


class OperatorTC(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.n = RtlNetlist()

    def test_BoolNot(self):
        for v in [True, False]:
            res = ~hBool(v)
            self.assertEqual(res.val, not v)
            self.assertEqual(res.vld_mask, 1)

    def test_BitNot(self):
        for v in [False, True]:
            res = ~hBit(v)

            self.assertEqual(res.val, int(not v))
            self.assertEqual(res.vld_mask, 1)

    def _test_And(self, vals):
        for a, b, expected in andTable:
            res = vals[a] & vals[b]
            expectedRes = vals[expected]

            if isinstance(expectedRes, RtlSignalBase):
                self.assertIs(res, expectedRes)
            else:
                self.assertEqual(expectedRes.val, res.val,
                                 "%r & %r  val=%r (should be %r)"
                                 % (a, b, res.val, expectedRes.val))
                self.assertEqual(expectedRes.vld_mask, res.vld_mask,
                                 "%r & %r  vld_mask=%r (should be %r)"
                                 % (a, b, res.vld_mask, expectedRes.vld_mask))

    def _test_Or(self, vals):
        for a, b, expected in orTable:
            res = vals[a] | vals[b]
            expectedRes = vals[expected]

            if isinstance(expectedRes, RtlSignalBase):
                self.assertIs(res, expectedRes)
            else:
                self.assertEqual(expectedRes.val, res.val,
                                 "%r | %r  val=%r (should be %r)"
                                 % (a, b, res.val, expectedRes.val))
                self.assertEqual(expectedRes.vld_mask, res.vld_mask,
                                 "%r | %r  vld_mask=%r (should be %r)"
                                 % (a, b, res.vld_mask, expectedRes.vld_mask))

    def _test_Xor(self, vals):
        for a, b, expected in xorTable:
            res = vals[a] ^ vals[b]
            expectedRes = vals[expected]

            if isinstance(expectedRes, RtlSignalBase):
                self.assertIs(res, expectedRes)
            else:
                if expectedRes.vld_mask:
                    self.assertEqual(expectedRes.val, res.val,
                                     "%r ^ %r  val=%r (should be %r)"
                                     % (a, b, res.val, expectedRes.val))
                self.assertEqual(expectedRes.vld_mask, res.vld_mask,
                                 "%r ^ %r  vld_mask=%r (should be %r)"
                                 % (a, b, res.vld_mask, expectedRes.vld_mask))

    def test_BoolAnd(self):
        self._test_And(boolvals)

    def test_BitAnd(self):
        self._test_And(bitvals)

    def test_BoolOr(self):
        self._test_Or(boolvals)

    def test_BitOr(self):
        self._test_Or(bitvals)

    def test_BoolXor(self):
        self._test_Xor(boolvals)

    def test_BitXor(self):
        self._test_Xor(bitvals)

    def test_notNotIsOrigSig(self):
        a = self.n.sig("a")
        self.assertIs(a, ~ ~a)

    def test_downto(self):
        a = self.n.sig('a', dtype=INT)
        a.def_val = hInt(10)
        b = hInt(0)
        r = downtoFn(a, b)
        res = r.staticEval()
        self.assertEqual(int(res.val.start), 10)
        self.assertEqual(int(res.val.stop), 0)
        self.assertEqual(int(res.val.step), -1)

    def test_to(self):
        a = self.n.sig('a', dtype=INT)
        a.def_val = hInt(10)
        b = hInt(0)
        r = toFn(a, b)
        res = r.staticEval()
        self.assertEqual(int(res.val.start), 10)
        self.assertEqual(int(res.val.stop), 0)
        self.assertEqual(int(res.val.step), 1)

    def test_ADD_InvalidOperands(self):
        a = self.n.sig('a', dtype=STR)
        b = self.n.sig('b')
        self.assertRaises(Exception, lambda: a + b)

    def test_ADD_IntBits(self):
        a = vec(7, 8)
        b = hInt(1)
        c = a + b
        self.assertEqual(c.val, 8)
        self.assertEqual(c.vld_mask, mask(8))

        a = vec(255, 8)
        b = hInt(1)
        c = a + b
        self.assertEqual(c.val, 0)
        self.assertEqual(c.vld_mask, mask(8))

        a = vec(7, 8, False)
        b = hInt(1)
        c = a + b
        self.assertEqual(c.val, 8)
        self.assertEqual(c.vld_mask, mask(8))

        a = vec(255, 8, False)
        b = hInt(1)
        c = a + b
        self.assertEqual(c.val, 0)
        self.assertEqual(c.vld_mask, mask(8))

    def test_AND_eval(self):
        for a_in, b_in, out in [(0, 0, 0),
                                (0, 1, 0),
                                (1, 0, 0),
                                (1, 1, 1)]:
            res = hBit(a_in) & hBit(b_in)
            self.assertEqual(res.vld_mask, 1)
            self.assertEqual(
                res.val, out,
                "a_in %d, b_in %d, out %d"
                % (a_in, b_in, out))

    def test_ADD_eval(self):
        for a_in, b_in, out in [(0, 0, 0),
                                (0, 1, 1),
                                (1, 0, 1),
                                (1, 1, 2)]:
            res = hInt(a_in) + hInt(b_in)

            b_w = 2

            self.assertTrue(res.vld_mask)
            self.assertEqual(
                res.val, out,
                "a_in %d, b_in %d, out %d"
                % (a_in, b_in, out))

            resBit = vec(a_in, b_w) + vec(b_in, b_w)
            self.assertEqual(resBit.vld_mask, 3)
            self.assertEqual(
                resBit.val, out,
                "a_in %d, b_in %d, out %d"
                % (a_in, b_in, out))

    def test_bits_le(self):
        a = vec(8, 8)
        b = vec(16, 8)
        self.assertTrue((a <= b).val)
        self.assertFalse((b <= a).val)

    def test_bits_sig_slice_on_slice(self):
        n = RtlNetlist()
        s = n.sig("s", Bits(16))
        self.assertIs(s[10:0][2:0], s[2:0])
        self.assertIs(s[10:0][4:1], s[4:1])
        self.assertIs(s[12:5][4:1], s[9:6])

    def test_bits_sig_slice_on_slice_of_slice(self):
        n = RtlNetlist()
        s = n.sig("s", Bits(16))
        self.assertIs(s[10:0][7:0][2:0], s[2:0])
        self.assertIs(s[10:0][7:0][4:1], s[4:1])
        self.assertIs(s[12:5][7:1][4:1], s[10:7])

    def test_bits_mul(self):
        n = RtlNetlist()
        s = n.sig("s", Bits(16))
        s * 10
        s * s

    def test_array_eq_neq(self):
        t = Bits(8)[5]
        v0 = t.from_py(range(5))
        v1 = t.from_py({0: 10, 1: 2})
        v2 = t.from_py([1, 2, 3, 4, 5])

        self.assertTrue(v0._eq(v0))
        with self.assertRaises(ValueError):
            self.assertNotEqual(v0, v1)
        self.assertNotEqual(v0, v2)
        with self.assertRaises(ValueError):
            self.assertNotEqual(v1, v2)
        with self.assertRaises(ValueError):
            self.assertNotEqual(v1, v1)
        self.assertTrue(v2, v2)

    def test_int_neg(self):
        self.assertEqual(int(INT.from_py(-10)), -10)
        self.assertEqual(int(-INT.from_py(10)), -10)
        self.assertEqual(int(-INT.from_py(10)), -10)
        v = -INT.from_py(None)
        self.assertEqual(v.val, 0)
        self.assertEqual(v.vld_mask, 0)

    def test_int_to_bool(self):
        self.assertFalse(bool(INT.from_py(0)._auto_cast(BOOL)))
        self.assertTrue(bool(INT.from_py(1)._auto_cast(BOOL)))
        self.assertTrue(bool(INT.from_py(-11)._auto_cast(BOOL)))
        self.assertTrue(bool(INT.from_py(500)._auto_cast(BOOL)))

        with self.assertRaises(ValueError):
            bool(INT.from_py(None)._auto_cast(BOOL))


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(OperatorTC('test_bits_sig_slice_on_slice_of_slice'))
    suite.addTest(unittest.makeSuite(OperatorTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
