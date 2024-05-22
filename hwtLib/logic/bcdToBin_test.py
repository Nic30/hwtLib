#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.logic.bcdToBin import BcdToBin
from hwtSimApi.constants import CLK_PERIOD


def bin_to_bcd(v: int, digits: int):
    _v = v
    bcd = 0
    for i in range(digits):
        bcd |= (v % 10) << (i * 4)
        v //= 10

    assert v == 0, ("Not enough digits", _v, digits)
    return bcd


class BcdToBinTC(SimTestCase):
    CLK_PERIOD = CLK_PERIOD

    @classmethod
    def setUpClass(cls):
        cls.dut = BcdToBin()
        cls.dut.BCD_DIGITS = 3
        cls.compileSim(cls.dut)

    def test_0to127(self):
        dut = self.dut

        N = 128
        dut.din._ag.data.extend([bin_to_bcd(i, dut.BCD_DIGITS) for i in range(N)])
        self.runSim(self.CLK_PERIOD * 13 * N)

        res = dut.dout._ag.data
        self.assertEqual(len(res), N)
        for i, d in enumerate(res):
            self.assertValEqual(d, i)

    def test_128to255(self):
        dut = self.dut
        dut.din._ag.data.extend([bin_to_bcd(i, dut.BCD_DIGITS) for i in range(128, 256)])
        N = 256 - 128

        self.runSim(self.CLK_PERIOD * 13 * N)

        res = dut.dout._ag.data
        self.assertEqual(len(res), N)
        for i, d in enumerate(res):
            i += 128
            self.assertValEqual(d, i)

    def test_r_96to150(self):
        dut = self.dut
        dut.din._ag.data.extend([bin_to_bcd(i, dut.BCD_DIGITS) for i in range(96, 150)])
        N = 150 - 96
        self.randomize(dut.din)
        self.randomize(dut.dout)
        self.runSim(self.CLK_PERIOD * 13 * 2 * N)

        res = dut.dout._ag.data
        self.assertEqual(len(res), N)
        for i, d in enumerate(res):
            i += 96
            self.assertValEqual(d, i)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([BcdToBinTC("test_split")])
    suite = testLoader.loadTestsFromTestCase(BcdToBinTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
