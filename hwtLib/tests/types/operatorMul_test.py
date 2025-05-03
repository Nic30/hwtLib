import unittest

from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import INT
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from pyMathBitPrecise.bit_utils import to_signed

class OperatorMulTC(unittest.TestCase):

    def test_HBits_mul(self):
        n = RtlNetlist()
        s = n.sig("s", HBits(16))
        self.assertEqual((s * 10)._dtype.bit_length(), 16)
        self.assertEqual((s * s)._dtype.bit_length(), 16)
        self.assertEqual(int(INT.from_py(10) * INT.from_py(11)), 10 * 11)

    def test_HBits_mul_s_u_diff(self):
        b4_t = HBits(4)
        b4s_t = HBits(4, signed=True)

        for a in range(2 ** 4):
            for b in range(2 ** 4):
                _aU = b4_t.from_py(a)
                _aS = b4s_t.from_py(to_signed(a, 4))

                _bU = b4_t.from_py(b)
                _bS = b4s_t.from_py(to_signed(b, 4))
                
                # for lower width-bits of mul result it does not matter 
                # if multiplication is signed or unsigned
                resU = (a * b) & 0xf
                self.assertEqual(int(_aU * _bU), resU)
                self.assertEqual(int((_aU._zext(8) * _bU._zext(8))._trunc(4)), resU)
                self.assertEqual(int((_aU._sext(8) * _bU._sext(8))._trunc(4)), resU)

                aS = to_signed(a, 4)
                bS = to_signed(b, 4)
                resS = to_signed((aS * bS) & 0xf, 4)
                self.assertEqual(int(_aS * _bS), resS)
                self.assertEqual(int((_aS._zext(8) * _bS._zext(8))._trunc(4)), resS)
                self.assertEqual(int((_aS._sext(8) * _bS._sext(8))._trunc(4)), resS)


    # def assertEqual(self, first, second, msg=None):
    #    BitsSlicingTC.assertEqual(self, first, second, msg=msg)
    #
    # def assertStrEq(self, first, second, msg=None, serializer=Vhdl2008Serializer):
    #    BitsSlicingTC.assertStrEq(self, first, second, msg, serializer)
    #
    # def assertStrEqV(self, first, second, msg=None):
    #    BitsSlicingTC.assertStrEqV(self, first, second, msg)
    #
    # def assertStrEqC(self, first, second, msg=None):
    #    BitsSlicingTC.assertStrEqV(self, first, second, msg)
    #
    # def test_mul_to_mul_s(self):
    #    n = RtlNetlist()
    #    aS = n.sig("aS", int8_t, def_val=127)
    #    bS = n.sig("bS", int8_t, def_val=127)
    #
    #    c = aS * bS
    #    self.assertStrEq(c, "aS*bS")
    #    self.assertStrEqV(c, "sigV[3:0]")
    #    self.assertStrEqC(c, "static_cast<sc_uint<4>>(sigV.read())")
    #


if __name__ == '__main__':
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([OperatorMulTC("test_bitwiseSigReduce")])
    suite = testLoader.loadTestsFromTestCase(OperatorMulTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
