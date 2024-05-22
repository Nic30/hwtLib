#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hwIOs.std import HwIODataRdVld
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import HConstSequenceToInts
from hwtLib.handshaked.joinFair import HsJoinFairShare
from hwtSimApi.constants import CLK_PERIOD


def dataFn(d):
    return d._ag.data


class HsJoinFair_2inputs_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = HsJoinFairShare(HwIODataRdVld)
        cls.INPUTS = 2
        dut.INPUTS = cls.INPUTS
        dut.DATA_WIDTH = 8
        dut.EXPORT_SELECTED = True
        cls.compileSim(dut)

    def addToAllInputs(self, n):
        dut = self.dut
        for i, d in enumerate(dut.dataIn):
            d._ag.data.extend([_i + (n * i) for _i in range(n)])

        expected = []
        for d in zip(*map(dataFn, dut.dataIn)):
            expected.extend(d)

        return expected

    def test_passdata(self):
        dut = self.dut
        expected = self.addToAllInputs(6)

        self.runSim(self.INPUTS * 6 * 2 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.dataOut._ag.data, expected)

        for d in dut.dataIn:
            self.assertSequenceEqual([], d._ag.data)

        expSelected = [1 << (i % self.INPUTS) for i in range(self.INPUTS * 6)]
        self.assertValSequenceEqual(dut.selectedOneHot._ag.data,
                                    expSelected)

    def test_passdata_oneHasMore(self):
        dut = self.dut

        expected = self.addToAllInputs(6)

        d = [7, 8, 9, 10, 11, 12]
        dut.dataIn[self.INPUTS - 1]._ag.data.extend(d)
        expected.extend(d)

        self.runSim(self.INPUTS * 6 * 2 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.dataOut._ag.data, expected)

        for d in dut.dataIn:
            self.assertSequenceEqual([], d._ag.data)

        id0 = 1
        id1 = (1 << (self.INPUTS - 1))
        expSelected = [1 << (i % self.INPUTS) for i in range(self.INPUTS * 6)] + 6 * [id1, ]
        self.assertValSequenceEqual(dut.selectedOneHot._ag.data,
                                    expSelected)

    def test_passData_onLowPriority(self):
        dut = self.dut
        lowPriority = dut.dataIn[self.INPUTS - 1]
        expected = [_i for _i in range(6)]

        lowPriority._ag.data.extend(expected)

        self.runSim(12 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.dataOut._ag.data, expected)

        expSelected = [1 << (self.INPUTS - 1) for _ in range(6)]
        self.assertValSequenceEqual(dut.selectedOneHot._ag.data,
                                    expSelected)

    def test_randomized(self):
        dut = self.dut
        N = 8
        expected = []
        for i, inp in enumerate(dut.dataIn):
            self.randomize(inp)
            d = [i * N + i2 + 1 for i2 in range(N)]

            inp._ag.data.extend(d)
            expected.extend(d)

        self.randomize(dut.dataOut)

        self.runSim(self.INPUTS * N * 5 * CLK_PERIOD)

        self.assertEqual(set(HConstSequenceToInts(dut.dataOut._ag.data)),
                         set(expected))


class HsJoinFair_3inputs_TC(HsJoinFair_2inputs_TC):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = HsJoinFairShare(HwIODataRdVld)
        cls.INPUTS = 3
        dut.INPUTS = cls.INPUTS
        dut.DATA_WIDTH = 8
        cls.compileSim(dut)


if __name__ == "__main__":
    _ALL_TCs = [HsJoinFair_2inputs_TC, HsJoinFair_3inputs_TC]
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HsJoinFair_2inputs_TC("test_passdata")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
