#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest

from hwt.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.storedBurst import Axi4SStoredBurst
from pyMathBitPrecise.bit_utils import mask


class Axi4SStoredBurstTC(SimTestCase):

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def test_simple(self):
        DATA = [1, 2, 3, 4, 5, 6, 7, 8]
        dut = Axi4SStoredBurst()
        dut.DATA = DATA
        dut.USE_STRB = True
        dut.REPEAT = False
        self.compileSimAndStart(dut)
        self.randomize(dut.dataOut)

        self.runSim(20 * (len(DATA) + 2) * Time.ns)
        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    [(d, mask(8), int(d == DATA[-1]))
                                     for d in DATA])

    def test_repeated(self):
        DATA = [1, 2, 3, 4, 5, 6, 7, 8]
        dut = Axi4SStoredBurst()
        dut.DATA = DATA
        dut.USE_STRB = True
        dut.REPEAT = True
        self.compileSimAndStart(dut)
        self.randomize(dut.dataOut)

        self.runSim(20 * (len(DATA) * 2 + 2) * Time.ns)
        data = [(d, mask(8), d == DATA[-1]) for d in DATA]
        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    data * 2)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4SStoredBurstTC("test_normalOp")])
    suite = testLoader.loadTestsFromTestCase(Axi4SStoredBurstTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
