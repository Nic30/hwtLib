import unittest
from hwt.hdlObjects.types.bits import Bits
from hwtLib.types.ctypes import int8_t
from hwt.bitmask import mask
from hwt.simulator.agentConnector import valToInt


int512_t = Bits(width=512, signed=True)


class SignedArithmeticTC(unittest.TestCase):
    def getMinMaxVal(self, dtype):
        m = dtype.all_mask()
        intLow = -(m // 2) - 1
        intUp = m // 2
        return dtype.fromPy(intLow), dtype.fromPy(intUp), intLow, intUp

    def assertEqual(self, first, second, msg=None):
        if first is not None:
            first = int(first)

        if second is not None:
            second = int(second)

        return unittest.TestCase.assertEqual(self, first, second, msg=msg)

    def test_8b_proper_val(self, t=int8_t):
        self.assertEqual(t.fromPy(-1), -1)
        low, up, intLow, intUp = self.getMinMaxVal(t)

        self.assertEqual(low, intLow)

        self.assertEqual(up, intUp)

        # value is not pythonic value
        with self.assertRaises(AssertionError):
            t.fromPy(low - 1)

        with self.assertRaises(AssertionError):
            t.fromPy(up + 1)

        # value is out of range of type
        with self.assertRaises(AssertionError):
            t.fromPy(intLow - 1)

        with self.assertRaises(AssertionError):
            t.fromPy(intUp + 1)

    def test_8b_and(self, t=int8_t):
        low, up, intLow, intUp = self.getMinMaxVal(t)
        ut = Bits(t.bit_length())
        m = t.all_mask()

        v = t.fromPy(-1)
        self.assertEqual(v & ut.fromPy(m), -1)
        self.assertEqual(v & ut.fromPy(0), 0)
        self.assertEqual(v & ut.fromPy(1), 1)
        self.assertEqual(low & up, 0)
        self.assertEqual(low & -1, intLow)
        self.assertEqual(up & ut.fromPy(m), intUp)

    def test_8b_or(self, t=int8_t):
        ut = Bits(t.bit_length())
        m = t.all_mask()
        low, up, intLow, intUp = self.getMinMaxVal(t)

        v = t.fromPy(-1)
        self.assertEqual(v | ut.fromPy(m), -1)
        self.assertEqual(v | ut.fromPy(0), -1)

        self.assertEqual(low | ut.fromPy(m), -1)
        self.assertEqual(low | ut.fromPy(0), intLow)

        self.assertEqual(up | ut.fromPy(m), -1)
        self.assertEqual(up | ut.fromPy(0), intUp)

    def test_8b_xor(self, t=int8_t):
        ut = Bits(t.bit_length())
        m = t.all_mask()

        v = t.fromPy(-1)
        self.assertEqual(v ^ ut.fromPy(m), 0)
        self.assertEqual(v ^ ut.fromPy(0), -1)
        self.assertEqual(v ^ ut.fromPy(1), -2)

    def test_8b_invert(self, t=int8_t):
        low, up, intLow, intUp = self.getMinMaxVal(t)

        self.assertEqual(~t.fromPy(-1), 0)
        self.assertEqual(~low, intUp)
        self.assertEqual(~up, intLow)

    def test_8b_eq(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up, _, _ = self.getMinMaxVal(t)

        self.assertTrue(t.fromPy(-1)._eq(-1))
        self.assertTrue(t.fromPy(0)._eq(0))
        self.assertTrue(up._eq(up))
        self.assertTrue(low._eq(low))

        self.assertFalse(t.fromPy(0)._eq(-1))
        self.assertFalse(t.fromPy(-1)._eq(0))
        self.assertFalse(up._eq(low))
        self.assertFalse(low._eq(up))

        with self.assertRaises(TypeError):
            t.fromPy(0)._eq(ut.fromPy(0))

    def test_8b_ne(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up, _, _ = self.getMinMaxVal(t)

        self.assertFalse(t.fromPy(-1) != -1)
        self.assertFalse(t.fromPy(0) != 0)
        self.assertFalse(up != up)
        self.assertFalse(low != low)

        self.assertTrue(t.fromPy(0) != -1)
        self.assertTrue(t.fromPy(-1) != 0)
        self.assertTrue(up != low)
        self.assertTrue(low != up)

        with self.assertRaises(TypeError):
            t.fromPy(0) != ut.fromPy(0)

    def test_8b_lt(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up, _, _ = self.getMinMaxVal(t)

        self.assertFalse(t.fromPy(-1) < -1)
        self.assertFalse(t.fromPy(0) < 0)
        self.assertFalse(t.fromPy(1) < 1)
        self.assertFalse(up < up)
        self.assertFalse(low < low)

        self.assertFalse(t.fromPy(0) < -1)
        self.assertTrue(t.fromPy(-1) < 0)
        self.assertFalse(up < low)
        self.assertTrue(low < up)

        with self.assertRaises(TypeError):
            t.fromPy(0) < ut.fromPy(0)

    def test_8b_gt(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up, _, _ = self.getMinMaxVal(t)

        self.assertFalse(t.fromPy(-1) > -1)
        self.assertFalse(t.fromPy(0) > 0)
        self.assertFalse(t.fromPy(1) > 1)
        self.assertFalse(up > up)
        self.assertFalse(low > low)

        self.assertTrue(t.fromPy(0) > -1)
        self.assertFalse(t.fromPy(-1) > 0)
        self.assertTrue(up > low)
        self.assertFalse(low > up)

        with self.assertRaises(TypeError):
            t.fromPy(0) > ut.fromPy(0)

    def test_8b_ge(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up, _, _ = self.getMinMaxVal(t)

        self.assertTrue(t.fromPy(-1) >= -1)
        self.assertTrue(t.fromPy(0) >= 0)
        self.assertTrue(t.fromPy(1) >= 1)
        self.assertTrue(up >= up)
        self.assertTrue(low >= low)

        self.assertTrue(t.fromPy(0) >= -1)
        self.assertFalse(t.fromPy(-1) >= 0)
        self.assertTrue(up >= low)
        self.assertFalse(low >= up)

        with self.assertRaises(TypeError):
            t.fromPy(0) >= ut.fromPy(0)

    def test_8b_le(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up, _, _ = self.getMinMaxVal(t)

        self.assertTrue(t.fromPy(-1) <= -1)
        self.assertTrue(t.fromPy(0) <= 0)
        self.assertTrue(t.fromPy(1) <= 1)
        self.assertTrue(up <= up)
        self.assertTrue(low <= low)

        self.assertFalse(t.fromPy(0) <= -1)
        self.assertTrue(t.fromPy(-1) <= 0)
        self.assertFalse(up <= low)
        self.assertTrue(low <= up)

        with self.assertRaises(TypeError):
            t.fromPy(0) <= ut.fromPy(0)

    def test_8b_add(self, t=int8_t):
        low, up, intLow, intUp = self.getMinMaxVal(t)

        self.assertEqual(t.fromPy(-1) + -1, -2)
        self.assertEqual(t.fromPy(-1) + 0, -1)
        self.assertEqual(t.fromPy(1) + 0, 1)
        self.assertEqual(t.fromPy(-1) + 1, 0)
        self.assertEqual(low + 1, intLow + 1)
        self.assertEqual(low + -1, intUp)
        self.assertEqual(up + 1, intLow)
        self.assertEqual(up + -1, intUp - 1)

        self.assertEqual(t.fromPy(-10) + 20, 10)
        self.assertEqual(t.fromPy(10) + -20, -10)

    def test_8b_sub(self, t=int8_t):
        low, up, intLow, intUp = self.getMinMaxVal(t)

        self.assertEqual(t.fromPy(-1) - -1, 0)
        self.assertEqual(t.fromPy(-1) - 0, -1)
        self.assertEqual(t.fromPy(1) - 0, 1)
        self.assertEqual(t.fromPy(-1) - 1, -2)
        self.assertEqual(low - 1, intUp)
        self.assertEqual(low - -1, intLow + 1)
        self.assertEqual(up - 1, intUp - 1)
        self.assertEqual(up - -1, intLow)

        self.assertEqual(t.fromPy(-10) - 20, -30)
        self.assertEqual(t.fromPy(10) - -20, 30)

    def test_8b_cast(self, t=int8_t):
        w = t.bit_length()
        ut = Bits(w)

        self.assertEqual(int(t.fromPy(-1)._convert(ut)), mask(w))
        self.assertEqual(int(t.fromPy(-1)._unsigned()), mask(w))
        self.assertEqual(int(t.fromPy(-1)._vec()), mask(w))
        self.assertEqual(int(t.fromPy(1)._convert(ut)), 1)
        self.assertEqual(int(t.fromPy(0)._convert(ut)), 0)
        self.assertEqual(int(ut.fromPy(1)._convert(t)), 1)
        self.assertEqual(int(ut.fromPy(mask(w))._convert(t)), -1)
        self.assertEqual(int(ut.fromPy(mask(w))._signed()), -1)

    def test_8b_mul(self, t=int8_t):
        w = t.bit_length()
        low, up, _, _ = self.getMinMaxVal(t)
        ut = Bits(w)

        self.assertEqual(int(t.fromPy(-1) * t.fromPy(-1)), 1)
        self.assertEqual(int(t.fromPy(0) * t.fromPy(-1)), 0)
        self.assertEqual(int(ut.fromPy(0) * ut.fromPy(1)), 0)
        self.assertEqual(int(ut.fromPy(mask(w)) * ut.fromPy(2)), (mask(w) << 1) & mask(w))
        self.assertEqual(int(t.fromPy(-1) * ut.fromPy(2)), -2)
        self.assertEqual(low * t.fromPy(2), 0)
        self.assertEqual(up * t.fromPy(2), -2)

        m = up * t.fromPy(None)
        self.assertEqual(valToInt(m), None)

    def test_512b_proper_val(self):
        self.test_8b_proper_val(int512_t)

    def test_512b_and(self):
        self.test_8b_and(int512_t)

    def test_512b_or(self):
        self.test_8b_or(int512_t)

    def test_512b_xor(self):
        self.test_8b_xor(int512_t)

    def test_512b_invert(self):
        self.test_8b_invert(int512_t)

    def test_512b_eq(self):
        self.test_8b_eq(int512_t)

    def test_512b_ne(self):
        self.test_8b_ne(int512_t)

    def test_512b_lt(self):
        self.test_8b_lt(int512_t)

    def test_512b_gt(self):
        self.test_8b_gt(int512_t)

    def test_512b_le(self):
        self.test_8b_le(int512_t)

    def test_512b_ge(self):
        self.test_8b_ge(int512_t)

    def test_512b_add(self):
        self.test_8b_add(int512_t)

    def test_512b_sub(self):
        self.test_8b_sub(int512_t)

    def test_512b_cast(self):
        self.test_8b_cast(int512_t)

    def test_512b_mul(self):
        self.test_8b_mul(int512_t)

if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(OperatorTC('testBitAnd'))
    suite.addTest(unittest.makeSuite(SignedArithmeticTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
