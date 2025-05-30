#!/usr/bin/env python3alu
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.operatorDefs import downtoFn, toFn, HwtOps
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import INT, STR, BOOL
from hwt.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.tests.types.hConst_test import hBool, hBit, hInt, vec
from hwtLib.types.ctypes import uint8_t
from pyMathBitPrecise.bit_utils import mask


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
eqTable = [
    (None, None, None),
    (None, 0, None),
    (None, 1, None),
    (0, None, None),
    (0, 0, 1),
    (0, 1, 0),
    (1, 1, 1),
    (s0, 1, s0._eq(1)),
    (s0, 0, s0._eq(0)),
    (1, s0, hBit(1)._eq(s0)),
    (0, s0, hBit(0)._eq(s0)),
]

bitvals = {
    1: hBit(1),
    0: hBit(0),
    None: hBit(None),
    s0: s1,
    ~s0:~s1,
    hBit(1)._eq(s0): hBit(1)._eq(s1),
    hBit(0)._eq(s0): hBit(0)._eq(s1),
    s0._eq(1): s1._eq(1),
    s0._eq(0): s1._eq(0)
}

boolvals = {
    1: hBool(1),
    0: hBool(0),
    None: hBool(None),
    s0: s0,
    ~s0:~s0
}

COMMON_OPS = [
            HwtOps.DIV,
            HwtOps.ADD,
            HwtOps.SUB,
            HwtOps.MUL,
            HwtOps.XOR,
            HwtOps.AND,
            HwtOps.OR,
            HwtOps.CONCAT,
            HwtOps.EQ,
            HwtOps.NE,
            HwtOps.GT,
            HwtOps.GE,
            HwtOps.LT,
            HwtOps.LE,
            HwtOps.INDEX,
        ]


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

    def _test_Eq(self, vals):
        for a, b, expected in eqTable:
            res = vals[a]._eq(vals[b])
            expectedRes = vals[expected]

            if isinstance(expectedRes, RtlSignalBase):
                self.assertIs(res, expectedRes, (a, b))
            else:
                if expectedRes.vld_mask:
                    self.assertEqual(expectedRes.val, res.val,
                                     "%r._eq(%r)  val=%r (should be %r)"
                                     % (a, b, res.val, expectedRes.val))
                self.assertEqual(expectedRes.vld_mask, res.vld_mask,
                                 "%r._eq(%r)  vld_mask=%r (should be %r)"
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

    def test_BitEq(self):
        self._test_Eq(bitvals)

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

    def test_array_eq_neq(self):
        t = HBits(8)[5]
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

    def test_bit2BoolConversion(self):
        e = self.n.sig("e")
        cond = e._auto_cast(BOOL)
        self.assertTrue(cond._rtlObjectOrigin.operator == HwtOps.EQ)
        self.assertEqual(cond._rtlObjectOrigin.operands[0], e, 1)

    def test_NotAnd(self):
        n = self.n
        a = n.sig("a")
        b = n.sig("b")
        aAndB = a & b
        notAAndB = ~aAndB
        self.assertEqual(notAAndB._rtlObjectOrigin.operator, HwtOps.NOT)
        cond = notAAndB._auto_cast(BOOL)

        self.assertEqual(cond._rtlObjectOrigin.operator, HwtOps.EQ)
        self.assertIs(cond._rtlObjectOrigin.operands[0], aAndB)
        self.assertEqual(int(cond._rtlObjectOrigin.operands[1]), 0)

        andOp = notAAndB._rtlObjectOrigin.operands[0]._rtlObjectOrigin
        self.assertEqual(andOp.operator, HwtOps.AND)

        op0 = andOp.operands[0]
        op1 = andOp.operands[1]

        self.assertEqual(op0, a)
        self.assertEqual(op1, b)

    def test_bitwiseSigReduce(self):
        n = self.n
        a = n.sig("a")
        self.assertEqual(a & a, a)
        self.assertEqual(int(a & ~a), 0)
        self.assertEqual(int(~a & a), 0)

        self.assertEqual(a | a, a)
        self.assertEqual(int(a | ~a), 1)
        self.assertEqual(int(~a | a), 1)

        self.assertEqual(int(a ^ a), 0)
        self.assertEqual(int(a ^ ~a), 1)
        self.assertEqual(int(~a ^ a), 1)

    def test_BitsSignalTypeErrors(self):
        n = self.n
        a = n.sig("a")
        for op in COMMON_OPS + [
                    HwtOps.POW,
                    HwtOps.UREM,
                    HwtOps.SREM,
                    HwtOps.DOWNTO,
                    HwtOps.TO,
                    HwtOps.CALL,
                ]:
            with self.assertRaises((TypeError, ValueError, AttributeError), msg=op):
                op._evalFn(a, "xyz")

    def test_const_OP_signal_Bits(self):
        n = self.n
        a = n.sig("a", dtype=uint8_t)
        _2 = uint8_t.from_py(2)
        for op in COMMON_OPS:
            b = op._evalFn(_2, a)
            c = op._evalFn(_2, a)
            self.assertIs(b, c)

        for op in COMMON_OPS:
            # creating new uint8_t value object
            _3 = uint8_t.from_py(3)
            b = op._evalFn(_3, a)
            c = op._evalFn(_3, a)
            self.assertIs(b, c)

if __name__ == '__main__':
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([OperatorTC("test_bitwiseSigReduce")])
    suite = testLoader.loadTestsFromTestCase(OperatorTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
