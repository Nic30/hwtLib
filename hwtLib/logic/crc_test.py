from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.logic.crcComb import CrcComb
from hwtLib.logic.crcPoly import CRC_32, CRC_1, CRC_16_CCITT, CRC_8_CCITT


class CrcCombTC(SimTestCase):

    def setUpCrc(self, poly, polyWidth, dataWidth=None):
        if dataWidth is None:
            dataWidth = polyWidth
        u = self.u = CrcComb()
        self.DATA_WIDTH = dataWidth
        self.POLY_WIDTH = polyWidth
        u.DATA_WIDTH.set(dataWidth)
        u.POLY_WIDTH.set(polyWidth)
        u.POLY.set(poly)
        self.prepareUnit(u)

    # def doHash(self, string):
    #    string = bytes(string)
    #    wordSize = self.DATA_WIDTH // 8
    #    assert len(string) % wordSize == 0
    #    # for s in grouper(wordSize, string):
    #    self.u.dataIn._ag.data.append(int.from_bytes(inp, byteorder='little'))

    def test_crc1(self):
        self.setUpCrc(CRC_1, 8, 8)
        u = self.u
        inp = b"a"

        u.dataIn._ag.data.append(int.from_bytes(inp, byteorder='little'))
        self.doSim(50 * Time.ns)

        crc = 97
        self.assertValSequenceEqual(u.dataOut._ag.data, [crc])

    def test_crc8(self):
        self.setUpCrc(CRC_8_CCITT, 8, 8)
        u = self.u
        inp = b"a"

        u.dataIn._ag.data.append(int.from_bytes(inp, byteorder='little'))
        self.doSim(50 * Time.ns)

        crc = 0x20
        self.assertValSequenceEqual(u.dataOut._ag.data, [crc])

    def test_crc32(self):
        self.setUpCrc(CRC_32, 32)
        u = self.u
        inp = b"aaaa"

        u.dataIn._ag.data.append(int.from_bytes(inp, byteorder='little'))
        self.doSim(50 * Time.ns)

        crc = 0xB0E91122

        self.assertValSequenceEqual(u.dataOut._ag.data, [crc])

    def test_crc16(self):
        self.setUpCrc(CRC_16_CCITT, 16)
        u = self.u
        inp = b"aa"

        u.dataIn._ag.data.append(int.from_bytes(inp, byteorder='little'))
        self.doSim(50 * Time.ns)

        crc = 0x449C
        self.assertValSequenceEqual(u.dataOut._ag.data, [crc])

#class CrcTC(CrcCombTC):
#    def setUpCrc(self, poly, polyWidth, dataWidth=None):
#        if dataWidth is None:
#            dataWidth = polyWidth
#        u = self.u = Crc()
#        self.DATA_WIDTH = dataWidth
#        self.POLY_WIDTH = polyWidth
#        u.DATA_WIDTH.set(dataWidth)
#        u.POLY_WIDTH.set(polyWidth)
#        u.POLY.set(poly)
#        self.prepareUnit(u)
#
#    def test_simple(self):
#        inp = "a"
#        # print(crc32(inp))
#

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(CrcCombTC('test_crc1'))
    # suite.addTest(CrcCombTC('test_crc8'))
    # suite.addTest(CrcCombTC('test_crc32'))
    suite.addTest(unittest.makeSuite(CrcCombTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    