#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import StringIO
import unittest

from hwt.hdl.value import HValue
from hwt.serializer.vhdl import Vhdl2008Serializer
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.types.ctypes import uint8_t
from hwtLib.tests.types.hvalue_test import hBit, vec




class BitsSlicingTC(unittest.TestCase):

    def assertEqual(self, first, second, msg=None):
        if not (isinstance(first, int) and isinstance(second, int)):
            if not isinstance(first, HValue):
                first = first.staticEval()

            if not isinstance(second, HValue):
                if isinstance(second, int):
                    first = int(first)
                    return unittest.TestCase.assertEqual(self, first,
                                                         second, msg=msg)
                else:
                    second = second.staticEval()

            first = (first.val, first.vld_mask, first._dtype.bit_length())
            second = (second.val, second.vld_mask, second._dtype.bit_length())

        unittest.TestCase.assertEqual(self, first, second, msg=msg)

    def assertStrEq(self, first, second, msg=None):
        to_hdl = Vhdl2008Serializer.TO_HDL_AST()
        hdl = to_hdl.as_hdl(first)
        buff = StringIO()
        ser = Vhdl2008Serializer.TO_HDL(buff)
        ser.visit_iHdlObj(hdl)
        first = buff.getvalue().replace(" ", "")
        unittest.TestCase.assertEqual(self, first, second, msg=msg)

    def test_slice_bits_sig(self):
        n = RtlNetlist()
        sig = n.sig("sig", uint8_t, def_val=128)

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
    # suite.addTest(BitsSlicingTC('test_slice_bits_sig'))
    suite.addTest(unittest.makeSuite(BitsSlicingTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
