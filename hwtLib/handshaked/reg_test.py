#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIODataRdVld
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.reg import HandshakedReg
from hwtSimApi.constants import CLK_PERIOD


class HandshakedRegL1D0TC(SimTestCase):
    LATENCY = 1
    DELAY = 0

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = HandshakedReg(HwIODataRdVld)
        dut.DELAY = cls.DELAY
        dut.LATENCY = cls.LATENCY
        cls.MAX_LATENCY = cls.LATENCY if isinstance(cls.LATENCY, int) else max(cls.LATENCY)
        cls.compileSim(dut)

    def test_passdata(self, N=20):
        dut = self.dut
        dut.dataIn._ag.data.extend(range(N))

        self.runSim((self.DELAY + self.MAX_LATENCY) * 2 * N * CLK_PERIOD)

        self.assertValSequenceEqual(dut.dataOut._ag.data, list(range(N)))
        self.assertValSequenceEqual([], dut.dataIn._ag.data)

    def test_r_passdata(self, N=20):
        dut = self.dut
        dut.dataIn._ag.data.extend(range(N))
        self.randomize(dut.dataIn)
        self.randomize(dut.dataOut)

        self.runSim((self.DELAY + self.MAX_LATENCY) * 4 * N * CLK_PERIOD)

        self.assertValSequenceEqual(dut.dataOut._ag.data, list(range(N)))
        self.assertValSequenceEqual([], dut.dataIn._ag.data)


class HandshakedRegL2D1TC(HandshakedRegL1D0TC):
    LATENCY = 2
    DELAY = 1


class HandshakedRegL1_2D0TC(HandshakedRegL1D0TC):
    LATENCY = (1, 2)
    DELAY = 0


HandshakedRegTCs = [
    HandshakedRegL1D0TC,
    HandshakedRegL2D1TC,
    HandshakedRegL1_2D0TC,
]

if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HandshakedRegL1D0TC("test_r_passdata")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in HandshakedRegTCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
