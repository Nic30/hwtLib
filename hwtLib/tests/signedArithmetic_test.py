import unittest
from hwt.hdlObjects.types.bits import Bits
from hwtLib.types.ctypes import int8_t
from hwt.bitmask import mask


int512_t = Bits(width=512, signed=True)


class SignedArithmeticTC(unittest.TestCase):
    def getMinMaxVal(self, dtype):
        m = dtype.all_mask()
        low = -(m // 2) - 1
        up = m // 2
        return low, up

    def test_8b_proper_val(self, t=int8_t):
        v = t.fromPy(-1)
        self.assertEqual(int(v), -1)
        low, up = self.getMinMaxVal(t)

        v = t.fromPy(low)
        self.assertEqual(int(v), low)

        v = t.fromPy(up)
        self.assertEqual(int(v), up)

        with self.assertRaises(AssertionError):
            t.fromPy(low - 1)

        with self.assertRaises(AssertionError):
            t.fromPy(up + 1)

    def test_8b_and(self, t=int8_t):
        v = t.fromPy(-1)
        ut = Bits(t.bit_length())
        m = t.all_mask()

        self.assertEqual(int(v & ut.fromPy(m)), -1)
        self.assertEqual(int(v & ut.fromPy(0)), 0)
        self.assertEqual(int(v & ut.fromPy(1)), 1)

    def test_8b_or(self, t=int8_t):
        v = t.fromPy(-1)
        ut = Bits(t.bit_length())
        m = t.all_mask()
        low, up = self.getMinMaxVal(t)

        self.assertEqual(int(v | ut.fromPy(m)), -1)
        self.assertEqual(int(v | ut.fromPy(0)), -1)

        v = t.fromPy(low)
        self.assertEqual(int(v | ut.fromPy(m)), -1)
        self.assertEqual(int(v | ut.fromPy(0)), low)

        v = t.fromPy(up)
        self.assertEqual(int(v | ut.fromPy(m)), -1)
        self.assertEqual(int(v | ut.fromPy(0)), up)

    def test_8b_xor(self, t=int8_t):
        v = t.fromPy(-1)
        ut = Bits(t.bit_length())
        m = t.all_mask()

        self.assertEqual(int(v ^ ut.fromPy(m)), 0)
        self.assertEqual(int(v ^ ut.fromPy(0)), -1)
        self.assertEqual(int(v ^ ut.fromPy(1)), -2)

    def test_8b_invert(self, t=int8_t):
        low, up = self.getMinMaxVal(t)

        self.assertEqual(int(~t.fromPy(-1)), 0)
        self.assertEqual(int(~t.fromPy(low)), up)
        self.assertEqual(int(~t.fromPy(up)), low)

    def test_8b_eq(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up = self.getMinMaxVal(t)

        self.assertTrue(t.fromPy(-1)._eq(-1))
        self.assertTrue(t.fromPy(0)._eq(0))
        self.assertTrue(t.fromPy(up)._eq(up))
        self.assertTrue(t.fromPy(low)._eq(low))

        self.assertFalse(t.fromPy(0)._eq(-1))
        self.assertFalse(t.fromPy(-1)._eq(0))
        self.assertFalse(t.fromPy(up)._eq(low))
        self.assertFalse(t.fromPy(low)._eq(up))

        with self.assertRaises(TypeError):
            t.fromPy(0)._eq(ut.fromPy(0))

    def test_8b_ne(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up = self.getMinMaxVal(t)

        self.assertFalse(t.fromPy(-1) != -1)
        self.assertFalse(t.fromPy(0) != 0)
        self.assertFalse(t.fromPy(up) != up)
        self.assertFalse(t.fromPy(low) != low)

        self.assertTrue(t.fromPy(0) != -1)
        self.assertTrue(t.fromPy(-1) != 0)
        self.assertTrue(t.fromPy(up) != low)
        self.assertTrue(t.fromPy(low) != up)

        with self.assertRaises(TypeError):
            t.fromPy(0) != ut.fromPy(0)

    def test_8b_lt(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up = self.getMinMaxVal(t)

        self.assertFalse(t.fromPy(-1) < -1)
        self.assertFalse(t.fromPy(0) < 0)
        self.assertFalse(t.fromPy(1) < 1)
        self.assertFalse(t.fromPy(up) < up)
        self.assertFalse(t.fromPy(low) < low)

        self.assertFalse(t.fromPy(0) < -1)
        self.assertTrue(t.fromPy(-1) < 0)
        self.assertFalse(t.fromPy(up) < low)
        self.assertTrue(t.fromPy(low) < up)

        with self.assertRaises(TypeError):
            t.fromPy(0) < ut.fromPy(0)

    def test_8b_gt(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up = self.getMinMaxVal(t)

        self.assertFalse(t.fromPy(-1) > -1)
        self.assertFalse(t.fromPy(0) > 0)
        self.assertFalse(t.fromPy(1) > 1)
        self.assertFalse(t.fromPy(up) > up)
        self.assertFalse(t.fromPy(low) > low)

        self.assertTrue(t.fromPy(0) > -1)
        self.assertFalse(t.fromPy(-1) > 0)
        self.assertTrue(t.fromPy(up) > low)
        self.assertFalse(t.fromPy(low) > up)

        with self.assertRaises(TypeError):
            t.fromPy(0) > ut.fromPy(0)

    def test_8b_ge(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up = self.getMinMaxVal(t)

        self.assertTrue(t.fromPy(-1) >= -1)
        self.assertTrue(t.fromPy(0) >= 0)
        self.assertTrue(t.fromPy(1) >= 1)
        self.assertTrue(t.fromPy(up) >= up)
        self.assertTrue(t.fromPy(low) >= low)

        self.assertTrue(t.fromPy(0) >= -1)
        self.assertFalse(t.fromPy(-1) >= 0)
        self.assertTrue(t.fromPy(up) >= low)
        self.assertFalse(t.fromPy(low) >= up)

        with self.assertRaises(TypeError):
            t.fromPy(0) >= ut.fromPy(0)

    def test_8b_le(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up = self.getMinMaxVal(t)

        self.assertTrue(t.fromPy(-1) <= -1)
        self.assertTrue(t.fromPy(0) <= 0)
        self.assertTrue(t.fromPy(1) <= 1)
        self.assertTrue(t.fromPy(up) <= up)
        self.assertTrue(t.fromPy(low) <= low)

        self.assertFalse(t.fromPy(0) <= -1)
        self.assertTrue(t.fromPy(-1) <= 0)
        self.assertFalse(t.fromPy(up) <= low)
        self.assertTrue(t.fromPy(low) <= up)

        with self.assertRaises(TypeError):
            t.fromPy(0) <= ut.fromPy(0)


    def test_8b_add(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up = self.getMinMaxVal(t)

        self.assertEqual(int(t.fromPy(-1) + -1), -2)
        self.assertEqual(int(t.fromPy(-1) + 0), -1)
        self.assertEqual(int(t.fromPy(1) + 0), 1)
        self.assertEqual(int(t.fromPy(-1) + 1), 0)
        self.assertEqual(int(t.fromPy(low) + 1), low + 1)
        self.assertEqual(int(t.fromPy(low) + -1), up)
        self.assertEqual(int(t.fromPy(up) + 1), low)
        self.assertEqual(int(t.fromPy(up) + -1), up - 1)

        self.assertEqual(int(t.fromPy(-10) + 20), 10)
        self.assertEqual(int(t.fromPy(10) + -20), -10)

    def test_8b_sub(self, t=int8_t):
        ut = Bits(t.bit_length())
        low, up = self.getMinMaxVal(t)

        self.assertEqual(int(t.fromPy(-1) - -1), 0)
        self.assertEqual(int(t.fromPy(-1) - 0), -1)
        self.assertEqual(int(t.fromPy(1) - 0), 1)
        self.assertEqual(int(t.fromPy(-1) - 1), -2)
        self.assertEqual(int(t.fromPy(low) - 1), up)
        self.assertEqual(int(t.fromPy(low) - -1), low + 1)
        self.assertEqual(int(t.fromPy(up) - 1), up - 1)
        self.assertEqual(int(t.fromPy(up) - -1), low)

        self.assertEqual(int(t.fromPy(-10) - 20), -30)
        self.assertEqual(int(t.fromPy(10) - -20), 30)

    def test_8b_cast(self, t=int8_t):
        w = t.bit_length()
        ut = Bits(w)
        
        self.assertEqual(int(t.fromPy(-1)._convert(ut)), mask(w))
        self.assertEqual(int(t.fromPy(1)._convert(ut)), 1)
        self.assertEqual(int(t.fromPy(0)._convert(ut)), 0)
        self.assertEqual(int(ut.fromPy(1)._convert(t)), 1)
        self.assertEqual(int(ut.fromPy(mask(w))._convert(t)), -1)
        

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

if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(OperatorTC('testBitAnd'))
    suite.addTest(unittest.makeSuite(SignedArithmeticTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
