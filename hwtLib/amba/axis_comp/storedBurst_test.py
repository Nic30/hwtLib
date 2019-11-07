#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.storedBurst import AxiSStoredBurst
from pyMathBitPrecise.bit_utils import mask


class AxiSStoredBurstTC(SimTestCase):

    def test_simple(self):
        DATA = [1, 2, 3, 4, 5, 6, 7, 8]
        u = AxiSStoredBurst(DATA)
        u.REPEAT = False
        self.compileSimAndStart(u)
        self.randomize(u.dataOut)

        self.runSim(20 * (len(DATA) + 2) * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(d, mask(8), int(d == DATA[-1]))
                                     for d in DATA])

    def test_repeated(self):
        DATA = [1, 2, 3, 4, 5, 6, 7, 8]
        u = AxiSStoredBurst(DATA)
        u.REPEAT = True
        self.compileSimAndStart(u)
        self.randomize(u.dataOut)

        self.runSim(20 * (len(DATA) * 2 + 2) * Time.ns)
        data = [(d, mask(8), d == DATA[-1]) for d in DATA]
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    data * 2)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(AxiSStoredBurstTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
