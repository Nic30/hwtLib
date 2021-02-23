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

    @classmethod
    def setUpClass(cls):
        cls.u = BcdToBin()
        cls.u.BCD_DIGITS = 3
        cls.compileSim(cls.u)

    def test_0to127(self):
        u = self.u

        N = 128
        u.din._ag.data.extend([bin_to_bcd(i, u.BCD_DIGITS) for i in range(N)])
        self.runSim(CLK_PERIOD * 13 * N)

        res = u.dout._ag.data
        self.assertEqual(len(res), N)
        for i, d in enumerate(res):
            self.assertValEqual(d, i)

    def test_128to255(self):
        u = self.u
        u.din._ag.data.extend([bin_to_bcd(i, u.BCD_DIGITS) for i in range(128, 256)])
        N = 256 - 128

        self.runSim(CLK_PERIOD * 13 * N)

        res = u.dout._ag.data
        self.assertEqual(len(res), N)
        for i, d in enumerate(res):
            i += 128
            self.assertValEqual(d, i)

    def test_r_96to150(self):
        u = self.u
        u.din._ag.data.extend([bin_to_bcd(i, u.BCD_DIGITS) for i in range(96, 150)])
        N = 150 - 96
        self.randomize(u.din)
        self.randomize(u.dout)
        self.runSim(CLK_PERIOD * 13 * 2 * N)

        res = u.dout._ag.data
        self.assertEqual(len(res), N)
        for i, d in enumerate(res):
            i += 96
            self.assertValEqual(d, i)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(IndexingTC('test_split'))
    suite.addTest(unittest.makeSuite(BcdToBinTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
