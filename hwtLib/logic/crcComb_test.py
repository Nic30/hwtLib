#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from binascii import crc32, crc_hqx
import os

from hwt.hdl.constants import Time
from hwt.hdl.typeShortcuts import vec
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.logic.crcComb import CrcComb
from hwtLib.logic.crcPoly import CRC_1, CRC_8_CCITT, CRC_16_CCITT, CRC_32, \
    CRC_8_SAE_J1850, CRC_5_USB
from pyMathBitPrecise.bit_utils import get_bit, bit_list_to_int, mask, \
    bit_list_reversed_endianity, bit_list_reversed_bits_in_bytes, reverse_bits


def stoi(s):
    if isinstance(s, str):
        s = s.encode()
    return int.from_bytes(s, byteorder='little')


def crcToBf(crc):
    return [get_bit(crc.POLY, i) for i in range(crc.WIDTH)]


def naive_crc(dataBits, crcBits, polyBits,
              refin=False, refout=False):
    crc_mask = CrcComb.buildCrcXorMatrix(len(dataBits), polyBits)

    dataBits = bit_list_reversed_endianity(dataBits)
    # print("")
    # for r in crc_mask:
    #    print(r)
    if refin:
        # reflect bytes in input data signal
        # whole signal should not be reflected if DW > PW
        # polyBits = list(reversed(polyBits))
        dataBits = bit_list_reversed_bits_in_bytes(dataBits)
        # crcBits = reversedBitsInBytes(crcBits)

    res = []
    for stateMask, dataMask in crc_mask:
        # if refin:
        #    stateMask = reversed(stateMask)
        #    dataMask = reversed(dataMask)

        v = 0
        for useBit, b in zip(stateMask, crcBits):
            if useBit:
                v ^= b

        for useBit, b in zip(dataMask, dataBits):
            if useBit:
                v ^= b

        res.append(v)

    assert len(res) == len(polyBits)
    if refout:
        res = reversed(res)
    return bit_list_to_int(res)


# http://www.sunshine2k.de/coding/javascript/crc/crc_js.html
class CrcCombTC(SimTestCase):

    def setUpCrc(self, poly, dataWidth=None,
                 refin=None,
                 refout=None,
                 initval=None,
                 finxor=None,
                 bigendian=False):
        if dataWidth is None:
            dataWidth = poly.WIDTH

        u = self.u = CrcComb()
        u.setConfig(poly)
        u.DATA_WIDTH = dataWidth
        if initval is not None:
            u.INIT = vec(initval, poly.WIDTH)
        if refin is not None:
            u.REFIN = refin
        if refout is not None:
            u.REFOUT = refout
        if finxor is not None:
            u.XOROUT = vec(finxor, poly.WIDTH)
        u.IN_IS_BIGENDIAN = bigendian
        self.compileSimAndStart(u)
        return u

    def test_crc1(self):
        self.setUpCrc(CRC_1, 8)
        u = self.u
        inp = b"a"

        u.dataIn._ag.data.append(stoi(inp))
        self.runSim(40 * Time.ns)

        crc = 1
        out = int(u.dataOut._ag.data[-1])
        self.assertEqual(out, crc, "0x{:x} 0x{:x}".format(crc, out))

    def test_crc8(self):
        self.setUpCrc(CRC_8_CCITT, 8)
        u = self.u
        inp = b"a"

        u.dataIn._ag.data.append(stoi(inp))
        self.runSim(40 * Time.ns)

        crc = 0x20
        out = int(u.dataOut._ag.data[-1])
        self.assertEqual(out, crc, "0x{:x} 0x{:x}".format(crc, out))

    def test_crc32_py(self):
        self.assertEqual(crc32(b"aa"), crc32(b"a", crc32(b"a")))
        # ! self.assertEqual(crc32(b"abcdefgh"),
        #                    crc32(b"abcd", crc32(b"efgh")))
        self.assertEqual(crc32(b"abcdefgh"), crc32(b"efgh", crc32(b"abcd")))
        # ! self.assertEqual(crc32(b"abcdefgh"),
        #                    crc32(b"efgh") ^ crc32(b"abcd"))

        self.assertEqual(crc_hqx(b"aa", CRC_16_CCITT.INIT),
                         crc_hqx(b"a", crc_hqx(b"a", CRC_16_CCITT.INIT)))
        # ! self.assertEqual(crc_hqx(b"abcdefgh", 0),
        #                    crc_hqx(b"abcd", crc_hqx(b"efgh", 0)))
        self.assertEqual(crc_hqx(b"abcdefgh", CRC_16_CCITT.INIT),
                         crc_hqx(b"efgh", crc_hqx(b"abcd", CRC_16_CCITT.INIT)))
        # ! self.assertEqual(crc_hqx(b"abcdefgh", CRC_16_CCITT.INIT),
        #                    crc_hqx(b"efgh", CRC_16_CCITT.INIT) ^ crc_hqx(b"abcd", CRC_16_CCITT.INIT))

        crc8 = crcToBf(CRC_8_CCITT)
        crc8_aes = crcToBf(CRC_8_SAE_J1850)
        cur8 = [0 for _ in range(8)]

        c2 = [get_bit(0xC2, i) for i in range(8)]
        self.assertEqual(naive_crc(c2, cur8, crc8_aes), 0xF)

        c = [get_bit(ord("c"), i) for i in range(8)]
        self.assertEqual(naive_crc(c, cur8, crc8), 0x2E)

        cur8_half_1 = [get_bit(0x0f, i) for i in range(8)]
        self.assertEqual(naive_crc(c2, cur8_half_1, crc8_aes), 0xB4)
        self.assertEqual(naive_crc(c, cur8_half_1, crc8_aes), 0x8)

        ab = [get_bit(stoi("ab"), i) for i in range(16)]
        self.assertEqual(naive_crc(ab, cur8, crc8_aes), 0x7D)
        self.assertEqual(naive_crc(ab, cur8_half_1, crc8_aes), 0xDE)

        _12 = [get_bit(0x0102, i) for i in range(16)]
        self.assertEqual(naive_crc(_12, cur8, crc8_aes), 0x85)
        self.assertEqual(naive_crc(_12, cur8_half_1, crc8_aes), 0x26)

        self.assertEqual(naive_crc(_12, cur8_half_1, crc8_aes, refin=True),
                         0x6F)

        cur32 = [0 for _ in range(32)]
        _crc32 = crcToBf(CRC_32)
        self.assertEqual(naive_crc(c, cur32, _crc32), 0xA1E6E04E)
        _s = ("0x00000000 0x04C11DB7 0x09823B6E 0x0D4326D9\n"
              "0x130476DC 0x17C56B6B 0x1A864DB2 0x1E475005\n")
        assert len(_s) % 4 == 0
        s = stoi(_s)
        s = [get_bit(s, i) for i in range(len(_s) * 8)]
        self.assertEqual(naive_crc(s, cur32, _crc32), 0x59F59BE0)
        cur32_1 = [1 for _ in range(32)]
        self.assertEqual(naive_crc(s, cur32_1, _crc32), 0x141026C0)

        self.assertEqual(naive_crc(s, cur32, _crc32,
                                   refout=True), 0x07D9AF9A)
        self.assertEqual(naive_crc(s, cur32_1, _crc32,
                                   refout=True), 0x03640828)
        self.assertEqual(naive_crc(s, cur32, _crc32,
                                   refin=True), 0xAE007AB1)
        self.assertEqual(naive_crc(s, cur32_1, _crc32,
                                   refin=True), 0xE3E5C791)
        self.assertEqual(naive_crc(s, cur32, _crc32,
                                   refin=True, refout=True), 0x8D5E0075)
        self.assertEqual(naive_crc(s, cur32_1, _crc32,
                                   refin=True, refout=True), 0x89E3A7C7)
        self.assertEqual(naive_crc(s, cur32_1, _crc32,
                                   refin=True, refout=True) ^ 0xffffffff,
                         crc32(_s.encode()))

    def test_crc32(self):
        for i, inp in enumerate([b"abcd", b"0001"]):
            u = self.setUpCrc(CRC_32)
            u.dataIn._ag.data.append(
               stoi(inp),
            )
            self.runSim(100 * Time.ns, name=os.path.join(self.DEFAULT_LOG_DIR,
                                                        f"test_crc32_{i:d}.vcd"))
            out = int(u.dataOut._ag.data[-1])
            ref = crc32(inp) & mask(32)
            self.assertEqual(out, ref, f"0x{out:08X} 0x{ref:08X}")

    def test_crc32_64b(self):
        inp = b"abcdefgh"
        u = self.setUpCrc(CRC_32, dataWidth=64)
        u.dataIn._ag.data.append(stoi(inp))
        self.runSim(100 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        ref = crc32(inp) & 0xffffffff
        self.assertEqual(out, ref, f"0x{out:08X} 0x{ref:08X}")

    def test_crc16(self):
        for i, inp in enumerate([b"aa", b"ab", b"x6"]):
            self.setUpCrc(CRC_16_CCITT)
            u = self.u

            u.dataIn._ag.data.append(stoi(inp))
            self.runSim(100 * Time.ns, name=os.path.join(self.DEFAULT_LOG_DIR,
                                                        f"test_crc16_{i:d}.vcd"))

            # crc = 0x449C
            ref = crc_hqx(inp, CRC_16_CCITT.INIT)
            d = u.dataOut._ag.data[-1]
            self.assertValEqual(d, ref, (inp, "0x{:x} 0x{:x}".format(int(d), ref)))

    def test_crc5_usb(self):
        def lsb_first_to_msb_first(val):
            v = reverse_bits(val & 0b111, 3)
            v |= reverse_bits(val >> 3, 7) << 3
            return v

        for i, (inp, ref) in enumerate([
                # addr=3a, endp=a
                (0b10101000_111, 0b10111),
                # addr=3a, endp=a
                (0b01011100_101, 0b11100),
                # addr=70, endp=4
                (0b00001110_010, 0b01110),
                                        ]):
            ref = reverse_bits(ref, 5)

            self.setUpCrc(CRC_5_USB, dataWidth=7 + 4,
                          refin=False,  # because bits are already reflected in data
                          bigendian=True,
                          )
            u = self.u
            u.dataIn._ag.data.append(inp)
            trace_file = os.path.join(self.DEFAULT_LOG_DIR,
                                      f"test_crc5_usb_{i:d}.vcd")
            self.runSim(100 * Time.ns, name=trace_file)

            d = u.dataOut._ag.data[-1]
            _d = int(d)
            self.assertValEqual(d, ref, (i, f"{_d:05b} {ref:05b}"))


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    #suite.addTest(CrcCombTC('test_crc5_usb'))
    suite.addTest(unittest.makeSuite(CrcCombTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
