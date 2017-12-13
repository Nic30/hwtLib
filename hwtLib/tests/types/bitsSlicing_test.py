import unittest

from hwt.hdl.typeShortcuts import vec, hBit, hInt, hStr
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.value import Value
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.types.ctypes import uint8_t


class BitsSlicingTC(unittest.TestCase):

    def assertEqual(self, first, second, msg=None):
        if not (isinstance(first, int) and isinstance(second, int)):
            if not isinstance(first, Value):
                first = first.staticEval()

            if not isinstance(second, Value):
                if isinstance(second, int):
                    first = int(first)
                    return unittest.TestCase.assertEqual(self, first,
                                                         second, msg=msg)
                else:
                    second = second.staticEval()

            first = (first.val, first.vldMask, first._dtype.bit_length())
            second = (second.val, second.vldMask, second._dtype.bit_length())

        unittest.TestCase.assertEqual(self, first, second, msg=msg)

    def assertStrEq(self, first, second, msg=None):
        ctx = VhdlSerializer.getBaseContext()
        first = VhdlSerializer.asHdl(first, ctx).replace(" ", "")
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

    def test_BitsIndexOnSingleBit(self):
        t = Bits(1)
        v = t.fromPy(1)
        with self.assertRaises(TypeError):
            v[0]

        t = Bits(1, forceVector=True)
        v = t.fromPy(1)
        self.assertEqual(v[0], hBit(1))

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
        self.assertEqual(v, 5)

        v[p2] = 2
        self.assertEqual(v, 6)

        with self.assertRaises(TypeError):
            v[hInt(None)] = 2

        v[:] = 0
        self.assertEqual(v, 0)

        v[2] = 1
        self.assertEqual(v, 4)
        v[3:] = p
        self.assertEqual(v, 2)

        v._setitem__val(hInt(None), hInt(1))
        with self.assertRaises(ValueError):
            int(v)

        with self.assertRaises(TypeError):
            v[hStr("asfs")]

    def test_BitsMulInvalidType(self):
        t = Bits(8)
        v = t.fromPy(1)
        with self.assertRaises(TypeError):
            v * "a"


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(BitsSlicingTC('test_slice_bits_sig'))
    suite.addTest(unittest.makeSuite(BitsSlicingTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
