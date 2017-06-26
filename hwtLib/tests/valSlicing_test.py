import unittest
from hwtLib.types.ctypes import uint8_t
from hwt.hdlObjects.typeShortcuts import vec, hBit
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwt.hdlObjects.value import Value

class ValSlicingTC(unittest.TestCase):
    def assertEqual(self, first, second, msg=None):
        if not isinstance(first, Value):
            first = first.staticEval()
        if not isinstance(second, Value):
            second = second.staticEval()
        
        first = (first.val, first.vldMask, first._dtype.bit_length())
        second = (second.val, second.vldMask, second._dtype.bit_length())
        
        unittest.TestCase.assertEqual(self, first, second, msg=msg)
    
    def assertStrEq(self, first, second, msg=None):
        first = repr(first).replace(" ", "")
        unittest.TestCase.assertEqual(self, first, second, msg=msg)
    
    def test_slice_bits(self):
        v128 = uint8_t.fromPy(128)
        v1 = uint8_t.fromPy(1)
        
        with self.assertRaises(IndexError):
            self.assertEqual(v128[8], hBit(1))
        
        self.assertEqual(v128[7], hBit(1))
        self.assertEqual(v128[1], hBit(0))
        self.assertEqual(v128[0], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqual(v128[-1], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqual(v128[9:-1], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqual(v128[9:], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqual(v128[9:0], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqual(v128[0:], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqual(v128[0:0], hBit(0))
        
        
        self.assertEqual(v128[8:], v128)
        self.assertEqual(v128[8:0], v128)
        self.assertEqual(v128[:0], v128)
        self.assertEqual(v128[:1], vec(64, 7))
        self.assertEqual(v128[:2], vec(32, 6))
        self.assertEqual(v128[:7], vec(1, 1))
        
        self.assertEqual(v1[1:], vec(1, 1))
        self.assertEqual(v1[2:], vec(1, 2))
        self.assertEqual(v1[8:], vec(1, 8))

    def test_slice_bits_sig(self):
        n = RtlNetlist()
        sig = n.sig("sig", uint8_t, defVal=128)
        
        with self.assertRaises(IndexError):
            self.assertEqual(sig[8], hBit(1))
        
        self.assertEqual(sig[7], hBit(1))
        self.assertStrEq(sig[7], "sig(7)")
        
        self.assertEqual(sig[1], hBit(0))
        self.assertStrEq(sig[1], "sig(1)")

        self.assertEqual(sig[0], hBit(0))
        self.assertStrEq(sig[0], "sig(0)")

        with self.assertRaises(IndexError):
            self.assertEqual(sig[-1], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqual(sig[9:-1], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqual(sig[9:], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqual(sig[9:0], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqual(sig[0:], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqual(sig[0:0], hBit(0))
        
        self.assertEqual(sig[8:], sig)
        self.assertStrEq(sig[8:], "sig")
        
        self.assertEqual(sig[8:0], sig)
        self.assertStrEq(sig[8:0], "sig")

        self.assertEqual(sig[:0], sig)
        self.assertStrEq(sig[:0], "sig")
        
        self.assertEqual(sig[:1], vec(64, 7))
        self.assertStrEq(sig[:1], "sig(7DOWNTO1)")
        
        self.assertEqual(sig[:2], vec(32, 6))
        self.assertStrEq(sig[:2], "sig(7DOWNTO2)")
        
        self.assertEqual(sig[:7], vec(1, 1))
        self.assertStrEq(sig[:7], "sig(7DOWNTO7)")
        
        self.assertEqual(sig[7:6], vec(0, 1))
        self.assertStrEq(sig[7:6], "sig(6DOWNTO6)")

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(IpCorePackagerTC('test_sWithStartPadding'))
    suite.addTest(unittest.makeSuite(ValSlicingTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
