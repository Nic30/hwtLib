#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import StringIO
import unittest

from hwt.code import Concat
from hwt.hdl.const import HConst
from hwt.hdl.operatorDefs import HwtOps
from hwt.hdl.types.bits import HBits
from hwt.serializer.systemC import SystemCSerializer
from hwt.serializer.verilog import VerilogSerializer
from hwt.serializer.vhdl import Vhdl2008Serializer
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.tests.types.hConst_test import hBit, vec
from hwtLib.types.ctypes import uint8_t, int8_t


class BitsSlicingTC(unittest.TestCase):

    def assertEqualRes(self, first, second, msg=None):
        if not (isinstance(first, int) and isinstance(second, int)):
            if not isinstance(first, HConst):
                first = first.staticEval()

            if not isinstance(second, HConst):
                if isinstance(second, int):
                    first = int(first)
                    return unittest.TestCase.assertEqual(self, first,
                                                         second, msg=msg)
                else:
                    second = second.staticEval()

            first = (first.val, first.vld_mask, first._dtype.bit_length())
            second = (second.val, second.vld_mask, second._dtype.bit_length())

        unittest.TestCase.assertEqual(self, first, second, msg=msg)

    def assertStrEq(self, first, second, msg=None, serializer=Vhdl2008Serializer):
        to_hdl = serializer.TO_HDL_AST()
        hdl = to_hdl.as_hdl(first)
        buff = StringIO()
        ser = serializer.TO_HDL(buff)
        ser.visit_iHdlObj(hdl)
        first = buff.getvalue().replace(" ", "")
        unittest.TestCase.assertEqual(self, first, second, msg=msg)

    def assertStrEqV(self, first, second, msg=None):
        self.assertStrEq(first, second, msg=msg, serializer=VerilogSerializer)

    def assertStrEqC(self, first, second, msg=None):
        self.assertStrEq(first, second, msg=msg, serializer=SystemCSerializer)

    def test_slice_bits_sig(self):
        n = RtlNetlist()
        sigU = n.sig("sigU", uint8_t, def_val=128)

        with self.assertRaises(IndexError):
            self.assertEqual(sigU[8], hBit(1))

        self.assertEqualRes(sigU[7], hBit(1))
        self.assertStrEq(sigU[7], "sigU(7)")

        self.assertEqualRes(sigU[1], hBit(0))
        self.assertStrEq(sigU[1], "sigU(1)")

        self.assertEqualRes(sigU[0], hBit(0))
        self.assertStrEq(sigU[0], "sigU(0)")

        with self.assertRaises(IndexError):
            self.assertEqualRes(sigU[-1], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqualRes(sigU[9:-1], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqualRes(sigU[9:], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqualRes(sigU[9:0], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqualRes(sigU[0:], hBit(0))

        with self.assertRaises(IndexError):
            self.assertEqualRes(sigU[0:0], hBit(0))

        self.assertEqual(sigU[8:], sigU)
        self.assertStrEq(sigU[8:], "sigU")

        self.assertEqual(sigU[8:0], sigU)
        self.assertStrEq(sigU[8:0], "sigU")

        self.assertEqual(sigU[:0], sigU)
        self.assertStrEq(sigU[:0], "sigU")

        self.assertEqualRes(sigU[:1], vec(64, 7))
        self.assertStrEq(sigU[:1], "sigU(7DOWNTO1)")

        self.assertEqualRes(sigU[:2], vec(32, 6))
        self.assertStrEq(sigU[:2], "sigU(7DOWNTO2)")

        self.assertEqualRes(sigU[:7], vec(1, 1))
        self.assertStrEq(sigU[:7], "sigU(7DOWNTO7)")

        self.assertEqualRes(sigU[7:6], vec(0, 1))
        self.assertStrEq(sigU[7:6], "sigU(6DOWNTO6)")

        self.assertStrEq(sigU._trunc(4), "RESIZE(sigU,4)")

        sigS = n.sig("sigS", int8_t)
        self.assertStrEq(sigS._trunc(4), "RESIZE(sigS,4)")

        sigV = n.sig("sigV", HBits(8))
        self.assertStrEq(sigV._trunc(4), "sigV(3DOWNTO0)")
        self.assertStrEqV(sigV._trunc(4), "sigV[3:0]")
        self.assertStrEqC(sigV._trunc(4), "static_cast<sc_uint<4>>(sigV.read())")

        self.assertStrEq(sigU._sext(10), "UNSIGNED(RESIZE(SIGNED(sigU),10))")
        self.assertStrEq(sigS._sext(10), "RESIZE(sigS,10)")
        self.assertStrEq(sigV._sext(10), "STD_LOGIC_VECTOR(RESIZE(SIGNED(sigV),10))")

        self.assertStrEqV(sigU._sext(10), "{{2{sigU[7]}},sigU}")
        self.assertStrEqV(sigS._sext(10), "{{2{sigS[7]}},sigS}")
        self.assertStrEqV(sigV._sext(10), "{{2{sigV[7]}},sigV}")

        self.assertStrEqC(sigU._sext(10), "static_cast<sc_uint<10>>(static_cast<sc_int<8>>(sigU.read()))")
        self.assertStrEqC(sigS._sext(10), "static_cast<sc_int<10>>(sigS.read())")
        self.assertStrEqC(sigV._sext(10), "static_cast<sc_uint<10>>(static_cast<sc_int<8>>(sigV.read()))")

        self.assertStrEq(sigU._zext(10), "RESIZE(sigU,10)")
        self.assertStrEq(sigS._zext(10), "SIGNED(RESIZE(UNSIGNED(sigS),10))")
        self.assertStrEq(sigV._zext(10), "STD_LOGIC_VECTOR(RESIZE(UNSIGNED(sigV),10))")

        self.assertStrEqV(sigU._zext(10), "{2'b00,sigU}")
        self.assertStrEqV(sigS._zext(10), "{2'b00,sigS}")
        self.assertStrEqV(sigV._zext(10), "{2'b00,sigV}")

        self.assertStrEqC(sigU._zext(10), "static_cast<sc_uint<10>>(sigU.read())")
        self.assertStrEqC(sigS._zext(10), "static_cast<sc_int<10>>(static_cast<sc_uint<8>>(sigS.read()))")
        self.assertStrEqC(sigV._zext(10), "static_cast<sc_uint<10>>(sigV.read())")

    def test_slice_bits_signed(self):
        n = RtlNetlist()
        sigU = n.sig("sigU", uint8_t, def_val=128)
        sigI = n.sig("sigI", int8_t, def_val=64)
        
        self.assertEqual(sigU._trunc(4)._dtype.signed, False)
        self.assertEqual(sigI._trunc(4)._dtype.signed, True)
        self.assertStrEq(sigU._trunc(4), "RESIZE(sigU,4)")
        self.assertStrEq(sigI._trunc(4), "RESIZE(sigI,4)")

        self.assertStrEqV(sigU._trunc(4), "sigU[3:0]")
        self.assertStrEqV(sigI._trunc(4), "$signed(sigI[3:0])")

        self.assertEqual(sigU[8:4]._dtype.signed, False)
        self.assertEqual(sigI[8:4]._dtype.signed, True)

        self.assertStrEq(sigU[8:4], "sigU(7DOWNTO4)")
        self.assertStrEq(sigI[8:4], "sigI(7DOWNTO4)")
        
        self.assertStrEqV(sigU[8:4], "sigU[7:4]")
        self.assertStrEqV(sigI[8:4], "$signed(sigI[7:4])")

    def test_HBits_sig_slice_on_slice(self):
        n = RtlNetlist()
        s = n.sig("s", HBits(16))
        self.assertIs(s[10:0][2:0], s[2:0])
        self.assertIs(s[10:0][4:1], s[4:1])
        self.assertIs(s[12:5][4:1], s[9:6])

    def test_HBits_sig_slice_on_slice_of_slice(self):
        n = RtlNetlist()
        s = n.sig("s", HBits(16))
        self.assertIs(s[10:0][7:0][2:0], s[2:0])
        self.assertIs(s[10:0][7:0][4:1], s[4:1])
        self.assertIs(s[12:5][7:1][4:1], s[10:7])

    def test_HBits_concat_to_zext(self):
        n = RtlNetlist()
        a = n.sig("a", dtype=int8_t)
        zPrefix = HBits(4).from_py(0)
        c = zPrefix._concat(a)
        self.assertEqual(c, a._zext(8 + 4))

    def test_HBits_concat_to_sext(self):
        n = RtlNetlist()
        a = n.sig("a", dtype=int8_t)
        aMsb = a.getMsb()
        c = aMsb._concat(a)
        self.assertEqual(c, a._sext(8 + 1))

        aMsb2b = aMsb._concat(aMsb)
        self.assertEqual(aMsb2b, aMsb._sext(2))

        c = aMsb2b._concat(a)
        self.assertEqual(c, a._sext(8 + 2))

        c = aMsb._concat(aMsb._concat(a))
        self.assertEqual(c, a._sext(8 + 2))

    def test_HBits_slice_to_trunc(self):
        n = RtlNetlist()
        a = n.sig("a", dtype=int8_t)
        a0 = a[0]
        self.assertEqual(a0.singleDriver().operator, HwtOps.INDEX)
        a2 = a[2:]
        self.assertEqual(a2.singleDriver().operator, HwtOps.TRUNC)
        self.assertEqual(a2, a._trunc(2))
        self.assertEqual(a[3:], a._trunc(3))
        self.assertEqual(a[8:], a)

    def test_HBits_slice_concat_to_trunc(self):
        n = RtlNetlist()
        a = n.sig("a", dtype=HBits(8))
        b = n.sig("b", dtype=HBits(8))
        c = n.sig("c", dtype=HBits(8))
        d = Concat(c, b, a)
        for i in range(8):
            self.assertEqual(d[i], a[i])
            self.assertEqual(d[8 + i], b[i])
            self.assertEqual(d[2 * 8 + i], c[i])

        self.assertEqual(d[8:0], a)
        self.assertEqual(d[16:8], b)
        self.assertEqual(d[:16], c)

        self.assertEqual(d[4:0], a._trunc(4))
        self.assertEqual(d[12:8], b._trunc(4))
        self.assertEqual(d[20:16], c._trunc(4))

    def test_HBits_slice_zext(self):
        n = RtlNetlist()
        a = n.sig("a", dtype=HBits(8))
        b = a._zext(8 + 4)

        self.assertEqual(b[8:0], a)
        self.assertEqual(b[4:0], a._trunc(4))
        self.assertEqual(b[:8], HBits(4).from_py(0))
        self.assertEqual(b[10:6], a[:6]._zext(4))
        self.assertEqual(b[8:4], a[8:4])

    def test_HBits_slice_sext(self):
        n = RtlNetlist()
        a = n.sig("a", dtype=HBits(8))
        b = a._sext(8 + 4)

        self.assertEqual(b[8:0], a)
        self.assertEqual(b[4:0], a._trunc(4))
        self.assertEqual(b[:8], b.getMsb()._sext(4))
        self.assertEqual(b[10:6], a[:6]._sext(4))
        self.assertEqual(b[8:4], a[8:4])

    def test_HBits_concat_to_zext_in_concat(self):
        n = RtlNetlist()
        a = n.sig("a", dtype=HBits(8))
        c0 = HBits(3).from_py(0b111)
        c1 = HBits(9).from_py(0)
        b = Concat(a._zext(8 + 4), c0)
        c = Concat(c1, b)
        self.assertEqual(c, Concat(a._zext(8 + 4 + 9), c0))

        b = Concat(a._sext(8 + 4), c0)
        aMsb = a.getMsb()
        c = Concat(aMsb, b)
        self.assertEqual(c, Concat(a._sext(8 + 4 + 1), c0))


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([BitsSlicingTC("test_HBits_concat_to_zext_in_concat")])
    suite = testLoader.loadTestsFromTestCase(BitsSlicingTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
