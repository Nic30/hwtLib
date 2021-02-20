#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from binascii import crc32
import sys

from hwt.hdl.constants import Time
from hwt.pyUtils.arrayQuery import grouper
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.logic.crc import Crc
from hwtLib.logic.crcComb_test import stoi
from hwtLib.logic.crcPoly import CRC_32
from pyMathBitPrecise.bit_utils import mask
from hwt.hdl.types.bits import Bits


# , crc_hqx
# crc32 input reflected, result reflected,
# poly 0x4C11DB7, init 0xFFFFFFFF, final 0xFFFFFFFF
def pr(name, val):
    print("{:10s}:  0x{:08X} {:032b}".format(name, val, val))


C_240B = (b"\x00\x00\x00\x00"
          b"\x00\x00\x00\x00"
          b"\x00\x00\x00\x00"
          b"\x12\x34\x56\x78"
          b"\x00\x00\x00\x00"
          b"\x00\x00\x00\x00"
          b"\x00\x00\x00\x00"
          b"\xf0\xe0\xd0\xc3"
          b"\x00\x00\x00\x00"
          b"\xb9\xfd\xee\x5b"
          b"\x00\xff\x01\x02"
          b"\x03\x07\x00\x00"
          b"\x00\x00\x00\x00"
          b"\x00\x00\x00\x00"
          b"\x00\x00\x00\x00")


class CrcTC(SimTestCase):

    def setUpCrc(self, poly, dataWidth=None,
                 refin=None, refout=None,
                 initval=None, finxor=None,
                 use_mask=False,
                 is_bigendian=False):
        if dataWidth is None:
            dataWidth = poly.WIDTH

        u = self.u = Crc()
        u.setConfig(poly)
        if initval is not None:
            u.INIT = Bits(poly.WIDTH).from_py(initval)
        u.DATA_WIDTH = dataWidth
        if refin is not None:
            u.REFIN = refin
        if refout is not None:
            u.REFOUT = refout
        if finxor is not None:
            u.XOROUT = Bits(poly.WIDTH).from_py(finxor)
        u.MASK_GRANULARITY = 8 if use_mask else None
        u.IN_IS_BIGENDIAN = is_bigendian

        self.compileSimAndStart(u)
        return u

    def test_works_with_any_data_width(self):
        u = self.setUpCrc(CRC_32)
        u.dataIn._ag.data.append(stoi(b"aaaa"))
        self.runSim(20 * Time.ns)
        out32 = int(u.dataOut._ag.data[-1])

        u = self.setUpCrc(CRC_32, 16)
        u.dataIn._ag.data.extend([stoi(b"aa") for _ in range(2)])
        self.runSim(20 * Time.ns)
        out16 = int(u.dataOut._ag.data[-1])

        u = self.setUpCrc(CRC_32, 8)
        u.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(20 * Time.ns)
        out8 = int(u.dataOut._ag.data[-1])

        # print(f"32:{out32:x} 16:{out16:x} 8:{out8:x}")
        self.assertEqual(out32, out16)
        self.assertEqual(out16, out8)

    def test_simple(self):
        u = self.setUpCrc(CRC_32)
        inp = b"abcd"

        u.dataIn._ag.data.append(stoi(inp))
        # u.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(30 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_simple_mask_4_outof_4(self):
        u = self.setUpCrc(CRC_32, use_mask=True)
        inp = b"abcd"

        u.dataIn._ag.data.append((stoi(inp), mask(32 // 8), 1))
        # u.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(30 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_simple_mask_3_outof_4(self):
        u = self.setUpCrc(CRC_32, use_mask=True)
        inp = b"abc"

        u.dataIn._ag.data.append((stoi(inp), mask(24 // 8), 1))
        # u.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(30 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_simple_mask_7_outof_8(self):
        u = self.setUpCrc(CRC_32, use_mask=True)
        inp = b"abcdefg"

        u.dataIn._ag.data.extend([
            (stoi(inp[0:4]), mask(32 // 8), 0),
            (stoi(inp[4:]), mask(24 // 8), 1)
        ])
        # u.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(40 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_CRC32_0(self):
        u = self.setUpCrc(CRC_32)
        inp = b"\x00\x00\x00\x00"

        u.dataIn._ag.data.append(stoi(inp))
        # u.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(30 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_CRC32_dual_0(self):
        u = self.setUpCrc(CRC_32)
        inp = b"\x00\x00\x00\x00\x00\x00\x00\x00"

        u.dataIn._ag.data.extend([0, 0])
        # u.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(40 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_CRC32_wide_dual_0(self):
        rec_limit = sys.getrecursionlimit()
        # because there is too much of nested operators in this very large xor tree
        sys.setrecursionlimit(1500)
        try:
            u = self.setUpCrc(CRC_32, dataWidth=32 * 8)
        finally:
            sys.setrecursionlimit(rec_limit)
        u.dataIn._ag.data.extend([0, 0])
        self.runSim(50 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        inp = (0).to_bytes(2 * 32, byteorder="little")
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_3x32b(self):
        u = self.setUpCrc(CRC_32)
        u.dataIn._ag.data.extend([
            stoi("abcd"),
            stoi("efgh"),
            stoi("ijkl")
        ])
        ref = crc32("abcdefghijkl".encode())
        self.runSim(50 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_240B_CRC32_bare(self):
        u = self.setUpCrc(CRC_32, dataWidth=240,
                          refin=False, refout=False,
                          initval=0, finxor=0)

        u.dataIn._ag.data += [
            stoi(C_240B[:len(C_240B) // 2]),
            stoi(C_240B[len(C_240B) // 2:]),
        ]
        # print("\n")
        #
        # for _d in C_240B:
        #    print(f" 0x{_d:x}", end='')

        self.runSim(40 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        ref = 0x28A4D370
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_240B_CRC32_init(self):
        u = self.setUpCrc(CRC_32, dataWidth=240,
                          refin=False, refout=False,
                          finxor=0)

        u.dataIn._ag.data += [
            stoi(C_240B[:len(C_240B) // 2]),
            stoi(C_240B[len(C_240B) // 2:]),
        ]

        self.runSim(40 * Time.ns)
        out = int(u.dataOut._ag.data[-1])

        ref = 0xC7CA64AF
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_240B_CRC32_init_refout(self):
        u = self.setUpCrc(CRC_32, dataWidth=240,
                          refin=False, finxor=0)

        u.dataIn._ag.data += [
            stoi(C_240B[:len(C_240B) // 2]),
            stoi(C_240B[len(C_240B) // 2:]),
        ]

        self.runSim(40 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        ref = 0xF52653E3
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_240B_CRC32_init_refout_finxor(self):
        u = self.setUpCrc(CRC_32, dataWidth=240,
                          refin=False)

        u.dataIn._ag.data += [
            stoi(C_240B[:len(C_240B) // 2]),
            stoi(C_240B[len(C_240B) // 2:]),
        ]

        self.runSim(40 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        ref = 0x0AD9AC1C
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_240B(self):
        u = self.setUpCrc(CRC_32, dataWidth=240)

        u.dataIn._ag.data += [
            stoi(C_240B[:len(C_240B) // 2]),
            stoi(C_240B[len(C_240B) // 2:]),
        ]
        self.runSim(40 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        ref = crc32(C_240B)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_240B_CRC32_32b(self):
        u = self.setUpCrc(CRC_32)

        u.dataIn._ag.data += [stoi(d) for d in grouper(4, C_240B)]
        self.runSim((3 + len(u.dataIn._ag.data)) * 10 * Time.ns)
        out = int(u.dataOut._ag.data[-1])
        ref = crc32(C_240B)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(CrcTC('test_simple'))
    # suite.addTest(CrcTC('test_wide'))
    # suite.addTest(CrcTC('test_240B_CRC32_init_refout_finxor'))
    # suite.addTest(CrcTC('test_240B'))
    # suite.addTest(CrcTC("test_simple_mask_3_outof_4"))
    suite.addTest(unittest.makeSuite(CrcTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
