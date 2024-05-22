#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4s import Axi4Stream, axi4s_recieve_bytes, axi4s_send_bytes
from hwtLib.amba.axis_comp.strformat_fn import axiS_strFormat
from hwtLib.types.ctypes import uint8_t
from hwtSimApi.constants import CLK_PERIOD


class _example_Axi4S_strFormat_no_args(HwModule):

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(8)

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.out = Axi4Stream()._m()

    @override
    def hwImpl(self):
        o = axiS_strFormat(self, "f0", self.DATA_WIDTH, "test 1234")
        self.out(o)
        propagateClkRstn(self)


class _example_Axi4S_strFormat_args_numbers(_example_Axi4S_strFormat_no_args):

    @override
    def hwConfig(self):
        _example_Axi4S_strFormat_no_args.hwConfig(self)
        self.FORMAT = HwParam("0b{0:08b}, 0o{0:04o}, {0:03d}, 0x{0:02x}, 0x{0:02X}")

    @override
    def hwImpl(self):
        n = self._sig("n", dtype=uint8_t)
        n(13)
        o = axiS_strFormat(
            self, "f0", self.DATA_WIDTH,
            self.FORMAT,
            n)
        self.out(o)
        propagateClkRstn(self)


class _example_Axi4S_strFormat_kwargs_numbers(_example_Axi4S_strFormat_no_args):

    @override
    def hwConfig(self):
        _example_Axi4S_strFormat_no_args.hwConfig(self)
        self.FORMAT = "0b{arg0:08b}, 0o{arg0:04o}, {arg0:03d}, 0x{arg0:02x}, 0x{arg0:02X}"

    @override
    def hwImpl(self):
        n = self._sig("n", dtype=uint8_t)
        n(13)
        o = axiS_strFormat(
            self, "f0", self.DATA_WIDTH,
            self.FORMAT,
            arg0=n)
        self.out(o)
        propagateClkRstn(self)


class _example_Axi4S_strFormat_1x_str(HwModule):

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(8)

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.out = Axi4Stream()._m()
            self.str0 = Axi4Stream()

    @override
    def hwImpl(self):
        o = axiS_strFormat(self, "f0", self.DATA_WIDTH, "str0:{0:s}", self.str0)
        self.out(o)
        propagateClkRstn(self)


class _example_Axi4S_strFormat_3x_str(_example_Axi4S_strFormat_1x_str):

    @override
    def hwDeclr(self):
        super(_example_Axi4S_strFormat_3x_str, self).hwDeclr()
        with self._hwParamsShared():
            self.str1 = Axi4Stream()
            self.str2 = Axi4Stream()

    @override
    def hwImpl(self):
        o = axiS_strFormat(self, "f0", self.DATA_WIDTH, "{0:s}{1:s}xyz{str2:s}",
                           self.str0, self.str1, str2=self.str2)
        self.out(o)
        propagateClkRstn(self)


class Axi4S_strFormat_TC(SimTestCase):

    @override
    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def test_args_numbers(self):
        dut = self.compileSimAndStart(_example_Axi4S_strFormat_args_numbers())
        self.runSim(200 * CLK_PERIOD)

        for _ in range(3):
            frame = axi4s_recieve_bytes(dut.out)
            s = bytes(frame[1]).decode("utf-8")
            self.assertEqual(s, "0b{0:08b}, 0o{0:04o}, {0:03d}, 0x{0:02x}, 0x{0:02X}".format(13))

    def test_kwargs_numbers(self):
        dut = self.compileSimAndStart(_example_Axi4S_strFormat_kwargs_numbers())
        self.runSim(200 * CLK_PERIOD)

        for _ in range(3):
            frame = axi4s_recieve_bytes(dut.out)
            s = bytes(frame[1]).decode("utf-8")
            self.assertEqual(s, "0b{0:08b}, 0o{0:04o}, {0:03d}, 0x{0:02x}, 0x{0:02X}".format(13))

    def test_no_args(self):
        dut = self.compileSimAndStart(_example_Axi4S_strFormat_no_args())
        self.randomize(dut.out)
        self.runSim(50 * CLK_PERIOD)

        for _ in range(3):
            frame = axi4s_recieve_bytes(dut.out)
            s = bytes(frame[1]).decode("utf-8")
            self.assertEqual(s, 'test 1234')

    def test_1x_str(self):
        dut = self.compileSimAndStart(_example_Axi4S_strFormat_1x_str())
        self.randomize(dut.out)
        self.randomize(dut.str0)
        strings = ["test0", "x", "1234567890"]
        for s in strings:
            axi4s_send_bytes(dut.str0, s.encode("utf-8"))
        self.runSim(200 * CLK_PERIOD)

        for s_ref in strings:
            frame = axi4s_recieve_bytes(dut.out)
            s = bytes(frame[1]).decode("utf-8")
            self.assertEqual(s, "str0:{0:s}".format(s_ref))

    def test_3x_str(self):
        dut = self.compileSimAndStart(_example_Axi4S_strFormat_3x_str())
        self.randomize(dut.out)
        self.randomize(dut.str0)
        self.randomize(dut.str1)
        self.randomize(dut.str2)
        strings = [("test0", "str1", "str3"),
                   ("x", "y", "z"),
                   ("1234567890", "abc", "\t\n")]
        for s0, s1, s2 in strings:
            axi4s_send_bytes(dut.str0, s0.encode("utf-8"))
            axi4s_send_bytes(dut.str1, s1.encode("utf-8"))
            axi4s_send_bytes(dut.str2, s2.encode("utf-8"))
        self.runSim(200 * CLK_PERIOD)

        for s_ref in strings:
            frame = axi4s_recieve_bytes(dut.out)
            s = bytes(frame[1]).decode("utf-8")
            self.assertEqual(s, "{0:s}{1:s}xyz{2:s}".format(*s_ref))


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4S_strFormat_TC("test_args_numbers")])
    suite = testLoader.loadTestsFromTestCase(Axi4S_strFormat_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    # from hwt.synth import to_rtl_str
    # m = _example_Axi4S_strFormat_1x_str()
    # print(to_rtl_str(m))

