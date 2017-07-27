from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.logic.crcComb import CrcComb
from hwtLib.logic.crcPoly import CRC_32, CRC_1, CRC_16_CCITT, CRC_8_CCITT
from hwtLib.logic.crc import Crc
from binascii import crc32
from hwt.bitmask import mask  # , selectBit
from hwt.hdlObjects.typeShortcuts import vec
# from scapy.layers.sctp import crc32c
# from array import array

def stoi(s):
    return int.from_bytes(s, byteorder='little')
#
#
# def asUnsigned(val, width):
#    return val & mask(width)
#
# def inv(val):
#    width = 32
#    return asUnsigned(~val & mask(width), width)
#
# def reverseBits(val, width):
#    v = 0
#    for i in range(width):
#        v |= (selectBit(val, width - i - 1) << i)
#    return v
#
# CRC_32_2 = 0xEDB88320
#
# table = array('L')
# for byte in range(256):
#    crc = 0
#    for bit in range(8):
#        if (byte ^ crc) & 1:
#            crc = (crc >> 1) ^ CRC_32_2
#        else:
#            crc >>= 1
#        byte >>= 1
#    table.append(crc)
#
#
# def crc32_2(string):
#    value = 0xffffffff
#    for ch in string:
#        v = ord(ch)
#        value = table[(v ^ value) & 0xff] ^ (value >> 8)
#
#    return -1 - value
#
#
# def crc32_3(string):
#    value = 0xffffffff
#    for ch in string:
#        v = reverseBits(ord(ch), 8)
#        value = table[(v ^ value) & 0xff] ^ (value >> 8)
#
#    return -1 - value
#
#
# def crc32_4(string):
#    value = 0xffffffff
#    for ch in string:
#        v = ord(ch)
#        value = table[(v ^ value) & 0xff] ^ (value >> 8)
#
#    return value
#
#
# def crc32_5(string):
#    value = 0xffffffff
#    for ch in string:
#        v = reverseBits(ord(ch), 8)
#        value = table[(v ^ value) & 0xff] ^ (value >> 8)
#
#    return value


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

class CrcTC(SimTestCase):
    def setUpCrc(self, poly, polyWidth, dataWidth=None):
        if dataWidth is None:
            dataWidth = polyWidth
        u = self.u = Crc()

        self.DATA_WIDTH = dataWidth
        self.POLY_WIDTH = polyWidth
        # u.REVERSE_IN.set(True)
        u.REVERSE_OUT.set(True)
        
        m = vec(mask(polyWidth), polyWidth)
        u.FINAL_XOR_VAL.set(m)
        u.DATA_WIDTH.set(dataWidth)
        u.POLY_WIDTH.set(polyWidth)
        u.POLY.set(poly)
        u.SEED.set(m)

        self.prepareUnit(u)

        return u

    def test_works_with_any_data_width(self):
        poly = vec(CRC_32, 32)
        u = self.setUpCrc(poly, 32)
        u.dataIn._ag.data.append(stoi(b"aaaa"))
        self.doSim(50 * Time.ns)
        out32 = int(u.dataOut._ag.data[-1])
        
        u = self.setUpCrc(poly, 32, 16)
        u.dataIn._ag.data.extend([stoi(b"aa") for _ in range(2)])
        self.doSim(100 * Time.ns)
        out16 = int(u.dataOut._ag.data[-1])
        
        u = self.setUpCrc(poly, 32, 8)
        u.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.doSim(100 * Time.ns)
        out8 = int(u.dataOut._ag.data[-1])
        
        # print("32:%x" % out32, "16:%x" % out16, "8:%x" % out8)
        self.assertEqual(out32, out16)
        self.assertEqual(out16, out8)
        
        

    def test_simple(self):
        u = self.setUpCrc(vec(CRC_32, 32), 32)
        inp = b"aaaa"

        u.dataIn._ag.data.append(stoi(inp))
        # u.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.doSim(50 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        # print("%x" % stoi(inp))
        # print("crc32:    %x" % crc32(inp))
        # print("crc32_2:  %x" % asUnsigned(crc32_2("aaaa"), 32))
        # print("crc32_3:  %x" % asUnsigned(crc32_3("aaaa"), 32))
        # print("crc32_4:  %x" % asUnsigned(crc32_4("aaaa"), 32))
        #
        # print("~crc32:   %x" % inv(crc32(inp)))
        # print("~crc32_2: %x" % inv(crc32_2("aaaa")))
        # print("~crc32_3: %x" % inv(crc32_3("aaaa")))
        # print("~crc32_4: %x" % inv(crc32_4("aaaa")))
        #
        # print("crc32c:   %x" % crc32c([ord("a") for _ in range(4)]))
        # print("out:      %x" % out)
        # print("out_rev:  %x" % reverseBits(out, 32))
        # print("~out:     %x" % asUnsigned(~out, 32))
        # print("~out_rev: %x" % asUnsigned(~reverseBits(out, 32), 32))
        
        self.assertEqual(out, crc32(inp))


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(CrcCombTC('test_crc1'))
    # suite.addTest(CrcCombTC('test_crc8'))
    # suite.addTest(CrcCombTC('test_crc32'))
    suite.addTest(unittest.makeSuite(CrcCombTC))
    suite.addTest(unittest.makeSuite(CrcTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    
