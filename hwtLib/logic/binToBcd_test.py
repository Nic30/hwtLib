#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.logic.binToBcd import BinToBcd
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


def bcd_to_str(bcd: int, digits: int):
    digit_list = []
    for _ in range(digits):
        if bcd == 0:
            break
        d = bcd & mask(4)
        bcd >>= 4
        digit_list.append(f"{d:d}")

    if not digit_list:
        return "0"
    else:
        return "".join(reversed(digit_list))


class BinToBcdTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = BinToBcd()
        cls.dut.INPUT_WIDTH = 8
        cls.compileSim(cls.dut)

    def test_0to127(self):
        dut = self.dut

        N = 128
        dut.din._ag.data.extend(range(N))
        self.runSim(CLK_PERIOD * 11 * N)

        res = dut.dout._ag.data
        self.assertEqual(len(res), N)
        for i, d in enumerate(res):
            self.assertEqual(bcd_to_str(int(d), 3), f"{i:d}")

    def test_128to255(self):
        dut = self.dut
        dut.din._ag.data.extend(range(128, 256))
        N = 256 - 128

        self.runSim(CLK_PERIOD * 11 * N)

        res = dut.dout._ag.data
        self.assertEqual(len(res), N)
        for i, d in enumerate(res):
            i += 128
            self.assertEqual(bcd_to_str(int(d), 3), f"{i:d}")

    def test_r_96to150(self):
        dut = self.dut
        dut.din._ag.data.extend(range(96, 150))
        N = 150 - 96
        self.randomize(dut.din)
        self.randomize(dut.dout)
        self.runSim(CLK_PERIOD * 20 * N)

        res = dut.dout._ag.data
        self.assertEqual(len(res), N)
        for i, d in enumerate(res):
            i += 96
            self.assertEqual(bcd_to_str(int(d), 3), f"{i:d}")


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([BinToBcdTC("test_split")])
    suite = testLoader.loadTestsFromTestCase(BinToBcdTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
