import unittest
from hwt.hdlObjects.types.bits import Bits
from hwtLib.types.ctypes import int8_t


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

    def test_512b_proper_val(self):
        self.test_8b_proper_val(int512_t)

    def test_8b_and(self, t=int8_t):
        v = t.fromPy(-1)
        ut = Bits(t.bit_length())
        m = t.all_mask()

        self.assertEqual(int(v & ut.fromPy(m)), -1)
        self.assertEqual(int(v & ut.fromPy(0)), 0)
        self.assertEqual(int(v & ut.fromPy(1)), 1)

    def test_512b_and(self):
        self.test_8b_and(int512_t)

    def test_8b_or(self, t=int8_t):
        v = t.fromPy(-1)
        ut = Bits(t.bit_length())
        m = t.all_mask()
        up, low = self.getMinMaxVal(t)

        self.assertEqual(int(v | ut.fromPy(m)), -1)
        self.assertEqual(int(v | ut.fromPy(0)), -1)

        v = t.fromPy(low)
        self.assertEqual(int(v | ut.fromPy(m)), -1)
        self.assertEqual(int(v | ut.fromPy(0)), low)

        v = t.fromPy(up)
        self.assertEqual(int(v | ut.fromPy(m)), -1)
        self.assertEqual(int(v | ut.fromPy(0)), up)

    def test_512b_or(self):
        self.test_8b_or(int512_t)

    def test_8b_xor(self, t=int8_t):
        v = t.fromPy(-1)
        ut = Bits(t.bit_length())
        m = t.all_mask()

        self.assertEqual(int(v ^ ut.fromPy(m)), 0)
        self.assertEqual(int(v ^ ut.fromPy(0)), -1)
        self.assertEqual(int(v ^ ut.fromPy(1)), -2)

    def test_512b_xor(self):
        self.test_8b_xor(int512_t)

    def test_8b_invert(self, t=int8_t):
        up, low = self.getMinMaxVal(t)

        self.assertEqual(int(~t.fromPy(-1)), 0)
        self.assertEqual(int(~t.fromPy(low)), up)
        self.assertEqual(int(~t.fromPy(up)), low)

    def test_512b_invert(self):
        self.test_8b_invert(int512_t)

if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(OperatorTC('testBitAnd'))
    suite.addTest(unittest.makeSuite(SignedArithmeticTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
