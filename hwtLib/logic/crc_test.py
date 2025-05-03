#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from binascii import crc32
import sys

from hwt.constants import Time
from hwt.hdl.types.bits import HBits
from hwt.pyUtils.arrayQuery import grouper
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.logic.crc import Crc
from hwtLib.logic.crcComb_test import stoi
from hwtLib.logic.crcPoly import CRC_32
from pyMathBitPrecise.bit_utils import mask


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

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def setUpCrc(self, poly, dataWidth=None,
                 refin=None, refout=None,
                 initval=None, finxor=None,
                 use_mask=False,
                 is_bigendian=False):
        if dataWidth is None:
            dataWidth = poly.WIDTH

        dut = self.dut = Crc()
        dut.setConfig(poly)
        if initval is not None:
            dut.INIT = HBits(poly.WIDTH).from_py(initval)
        dut.DATA_WIDTH = dataWidth
        if refin is not None:
            dut.REFIN = refin
        if refout is not None:
            dut.REFOUT = refout
        if finxor is not None:
            dut.XOROUT = HBits(poly.WIDTH).from_py(finxor)
        dut.MASK_GRANULARITY = 8 if use_mask else None
        dut.IN_IS_BIGENDIAN = is_bigendian

        self.compileSimAndStart(dut)
        return dut

    def test_works_with_any_data_width(self):
        dut = self.setUpCrc(CRC_32)
        dut.dataIn._ag.data.append(stoi(b"aaaa"))
        self.runSim(20 * Time.ns)
        out32 = int(dut.dataOut._ag.data[-1])

        dut = self.setUpCrc(CRC_32, 16)
        dut.dataIn._ag.data.extend([stoi(b"aa") for _ in range(2)])
        self.runSim(20 * Time.ns)
        out16 = int(dut.dataOut._ag.data[-1])

        dut = self.setUpCrc(CRC_32, 8)
        dut.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(20 * Time.ns)
        out8 = int(dut.dataOut._ag.data[-1])

        # print(f"32:{out32:x} 16:{out16:x} 8:{out8:x}")
        self.assertEqual(out32, out16)
        self.assertEqual(out16, out8)

    def test_simple(self):
        dut = self.setUpCrc(CRC_32)
        inp = b"abcd"

        dut.dataIn._ag.data.append(stoi(inp))
        # dut.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(30 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_simple_mask_4_outof_4(self):
        dut = self.setUpCrc(CRC_32, use_mask=True)
        inp = b"abcd"

        dut.dataIn._ag.data.append((stoi(inp), mask(32 // 8), 1))
        # dut.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(30 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_simple_mask_3_outof_4(self):
        dut = self.setUpCrc(CRC_32, use_mask=True)
        inp = b"abc"

        dut.dataIn._ag.data.append((stoi(inp), mask(24 // 8), 1))
        # dut.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(30 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_simple_mask_7_outof_8(self):
        dut = self.setUpCrc(CRC_32, use_mask=True)
        inp = b"abcdefg"

        dut.dataIn._ag.data.extend([
            (stoi(inp[0:4]), mask(32 // 8), 0),
            (stoi(inp[4:]), mask(24 // 8), 1)
        ])
        # dut.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(40 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_CRC32_0(self):
        dut = self.setUpCrc(CRC_32)
        inp = b"\x00\x00\x00\x00"

        dut.dataIn._ag.data.append(stoi(inp))
        # dut.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(30 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_CRC32_dual_0(self):
        dut = self.setUpCrc(CRC_32)
        inp = b"\x00\x00\x00\x00\x00\x00\x00\x00"

        dut.dataIn._ag.data.extend([0, 0])
        # dut.dataIn._ag.data.extend([ord("a") for _ in range(4)])
        self.runSim(40 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_CRC32_wide_dual_0(self):
        rec_limit = sys.getrecursionlimit()
        # because there is too much of nested operators in this very large xor tree
        sys.setrecursionlimit(1500)
        try:
            dut = self.setUpCrc(CRC_32, dataWidth=32 * 8)
        finally:
            sys.setrecursionlimit(rec_limit)
        dut.dataIn._ag.data.extend([0, 0])
        self.runSim(50 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        inp = (0).to_bytes(2 * 32, byteorder="little")
        ref = crc32(inp)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_3x32b(self):
        dut = self.setUpCrc(CRC_32)
        dut.dataIn._ag.data.extend([
            stoi("abcd"),
            stoi("efgh"),
            stoi("ijkl")
        ])
        ref = crc32("abcdefghijkl".encode())
        self.runSim(50 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_240B_CRC32_bare(self):
        dut = self.setUpCrc(CRC_32, dataWidth=240,
                          refin=False, refout=False,
                          initval=0, finxor=0)

        dut.dataIn._ag.data += [
            stoi(C_240B[:len(C_240B) // 2]),
            stoi(C_240B[len(C_240B) // 2:]),
        ]
        # print("\n")
        #
        # for _d in C_240B:
        #    print(f" 0x{_d:x}", end='')

        self.runSim(40 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        ref = 0x28A4D370
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_240B_CRC32_init(self):
        dut = self.setUpCrc(CRC_32, dataWidth=240,
                          refin=False, refout=False,
                          finxor=0)

        dut.dataIn._ag.data += [
            stoi(C_240B[:len(C_240B) // 2]),
            stoi(C_240B[len(C_240B) // 2:]),
        ]

        self.runSim(40 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])

        ref = 0xC7CA64AF
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_240B_CRC32_init_refout(self):
        dut = self.setUpCrc(CRC_32, dataWidth=240,
                          refin=False, finxor=0)

        dut.dataIn._ag.data += [
            stoi(C_240B[:len(C_240B) // 2]),
            stoi(C_240B[len(C_240B) // 2:]),
        ]

        self.runSim(40 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        ref = 0xF52653E3
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_240B_CRC32_init_refout_finxor(self):
        dut = self.setUpCrc(CRC_32, dataWidth=240,
                          refin=False)

        dut.dataIn._ag.data += [
            stoi(C_240B[:len(C_240B) // 2]),
            stoi(C_240B[len(C_240B) // 2:]),
        ]

        self.runSim(40 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        ref = 0x0AD9AC1C
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_240B(self):
        dut = self.setUpCrc(CRC_32, dataWidth=240)

        dut.dataIn._ag.data += [
            stoi(C_240B[:len(C_240B) // 2]),
            stoi(C_240B[len(C_240B) // 2:]),
        ]
        self.runSim(40 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        ref = crc32(C_240B)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))

    def test_240B_CRC32_32b(self):
        dut = self.setUpCrc(CRC_32)

        dut.dataIn._ag.data += [stoi(d) for d in grouper(4, C_240B)]
        self.runSim((3 + len(dut.dataIn._ag.data)) * 10 * Time.ns)
        out = int(dut.dataOut._ag.data[-1])
        ref = crc32(C_240B)
        self.assertEqual(out, ref, "0x{:08X} 0x{:08X}".format(out, ref))


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    
    # suite = unittest.TestSuite([CrcTC("test_simple_mask_3_outof_4")])
    suite = testLoader.loadTestsFromTestCase(CrcTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
