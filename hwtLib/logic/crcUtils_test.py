import unittest

from hwt.bitmask import selectBit
from hwtLib.logic.crcUtils import buildCrcMatrix_dataMatrix, parsePolyStr
from hwtLib.logic.crcPoly import CRC_16_CCITT, CRC_32


class CrcUtilsTC(unittest.TestCase):

    def test_parsePolyStr(self):
        crc32_str = "x^26 + x^23 + x^22 + x^16 + x^12 + x^11 + x^10 + x^8 + x^7 + x^5 + x^4 + x^2 + x^1 + 1"
        poly = parsePolyStr(crc32_str, 32)
        expected = [selectBit(CRC_32, i) for i in range(32)]
        self.assertEqual(poly, expected)

    def test_buildCrcMatrix_dataMatrix(self):
        polyWidth = 16
        polyCoefs = [selectBit(CRC_16_CCITT, i) for i in range(polyWidth)]
        matrix = buildCrcMatrix_dataMatrix(polyCoefs, polyWidth, polyWidth)
        expected = [
                    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0],
                    [0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0],
                    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0],
                    [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1],
                    [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1],
                    [1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0],
                    [0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0],
                    [0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1],
                    [0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1],
                    [0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1],
                    [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0],
                    [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1],
                    [1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1],
                    [0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0],
                    ]
        self.assertEqual(len(matrix), len(expected))
        for m, e in zip(matrix, expected):
            self.assertSequenceEqual(m, e)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(CrcCombTC('test_crc1'))
    suite.addTest(unittest.makeSuite(CrcUtilsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
