#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hwIOs.std import HwIODataRdVld
from hwt.hwIOs.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.joinPrioritized import HsJoinPrioritized
from hwtSimApi.constants import CLK_PERIOD


class HsJoinWithReference(HsJoinPrioritized):

    def _declr(self):
        HsJoinPrioritized._declr(self)
        addClkRstn(self)


class HsJoinPrioritizedTC(SimTestCase):
    randomized = False

    @classmethod
    def setUpClass(cls):
        cls.dut = HsJoinWithReference(HwIODataRdVld)
        cls.dut.DATA_WIDTH = 8
        cls.compileSim(cls.dut)

    def test_passdata(self):
        dut = self.dut

        dut.dataIn[0]._ag.data.extend([1, 2, 3, 4, 5, 6])
        dut.dataIn[1]._ag.data.extend([7, 8, 9, 10, 11, 12])
        t = 20
        if self.randomized:
            t *= 2
        self.runSim(t * CLK_PERIOD)

        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

        for d in dut.dataIn:
            self.assertEmpty(d._ag.data)


class HsJoinPrioritized_randomized_TC(HsJoinPrioritizedTC):
    randomized = True

    def setUp(self):
        super(HsJoinPrioritized_randomized_TC, self).setUp()
        self.randomize(self.dut.dataOut)


if __name__ == "__main__":
    _ALL_TCs = [HsJoinPrioritizedTC, HsJoinPrioritized_randomized_TC]
    testLoader = unittest.TestLoader()
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
