#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.en import Axi4S_en
from pyMathBitPrecise.bit_utils import mask


class Axi4S_en_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = Axi4S_en()
        dut.USE_STRB = True
        cls.compileSim(dut)

    def test_break(self):
        m = mask(64 // 8)
        MAGIC = 987
        dut = self.dut
        dut.en._ag.data += [0]
        dut.dataIn._ag.data.append((MAGIC, m, 1))
        self.runSim(100 * Time.ns)
        self.assertEmpty(dut.dataOut._ag.data)

    def test_pass(self):
        m = mask(64 // 8)
        MAGIC = 987
        dut = self.dut
        dut.en._ag.data += [1]
        d = [(MAGIC + 1, m, 1),
             (MAGIC + 2, m, 0),
             (MAGIC + 3, m, 1),
             (MAGIC + 4, m, 0),
             (MAGIC + 5, m, 0),
             (MAGIC + 6, m, 1)
             ]
        dut.dataIn._ag.data.extend(d)
        self.runSim(100 * Time.ns)
        self.assertValSequenceEqual(dut.dataOut._ag.data, d)

    def test_passFirstBreakContinue(self):
        m = mask(64 // 8)
        MAGIC = 987
        dut = self.dut
        dut.en._ag.data += [1, 0, 0, 0, 1]
        d = [(MAGIC + 1, m, 1),
             (MAGIC + 2, m, 0),
             (MAGIC + 3, m, 1),
             (MAGIC + 4, m, 0),
             (MAGIC + 5, m, 0),
             (MAGIC + 6, m, 1)
             ]
        dut.dataIn._ag.data.extend(d)
        self.runSim(100 * Time.ns)
        self.assertValSequenceEqual(dut.dataOut._ag.data, d)

    def test_randomized(self):
        self.randomize(self.dut.dataIn)
        self.randomize(self.dut.dataOut)

        m = mask(64 // 8)
        MAGIC = 987
        dut = self.dut

        d = [(MAGIC + 1, m, 1),
             (MAGIC + 2, m, 0),
             (MAGIC + 3, m, 1),
             (MAGIC + 4, m, 0),
             (MAGIC + 5, m, 0),
             (MAGIC + 6, m, 1)
             ]
        dut.en._ag.data.extend([(i + 1) % 2 for i in range(20 * len(d))])
        dut.dataIn._ag.data.extend(d)
        self.runSim(200 * len(d) * Time.ns)
        self.assertValSequenceEqual(dut.dataOut._ag.data, d)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4S_en_TC("test_doubleField")])
    suite = testLoader.loadTestsFromTestCase(Axi4S_en_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
