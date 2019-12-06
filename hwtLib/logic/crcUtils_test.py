#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwtLib.logic.crcPoly import CRC_32
from hwtLib.logic.crcUtils import parsePolyStr
from pyMathBitPrecise.bit_utils import selectBit


class CrcUtilsTC(unittest.TestCase):

    def test_parsePolyStr(self):
        crc32_str = ("x^26 + x^23 + x^22 + x^16 + x^12 + x^11 + x^10 + x^8"
                     " + x^7 + x^5 + x^4 + x^2 + x^1 + 1")
        poly = parsePolyStr(crc32_str, 32)
        expected = [selectBit(CRC_32.POLY, i) for i in range(CRC_32.WIDTH)]
        self.assertEqual(poly, expected)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(CrcCombTC('test_crc1'))
    suite.addTest(unittest.makeSuite(CrcUtilsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
