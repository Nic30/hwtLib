#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.avalon.st import AvalonST
from hwtSimApi.constants import CLK_PERIOD


class AvalonStWire(HwModule):

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.dataIn = AvalonST()
        self.dataOut = AvalonST()._m()
        for i in (self.dataIn, self.dataOut):
            i.USE_EMPTY = True
            i.ERROR_WIDTH = 1
            i.maxChannel = 2
            

    @override
    def hwImpl(self):
        self.dataOut(self.dataIn)


class AvalonStAgentTC(SimTestCase):
    CLK = CLK_PERIOD

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = dut = AvalonStWire()
        cls.compileSim(dut)

    def test_nop(self):
        dut = self.dut
        self.runSim(CLK_PERIOD)

        self.assertValSequenceEqual(
            dut.dataOut._ag.data,
            []
        )

    def test_can_pass_data(self):
        dut = self.dut
        N = 10

        #channel, data, empty, error, startOfPacket, endOfPacket
        d = [(1, i, 0, 0, i == 0, i == N - 1) for i in range(N)]
        dut.dataIn._ag.data.extend(d)

        self.runSim((N + 10) * self.CLK)

        self.assertValSequenceEqual(
            dut.dataOut._ag.data,
            d
        )

    def test_can_pass_data_randomized(self):
        dut = self.dut
        N = 40

        #channel, data, empty, error, startOfPacket, endOfPacket
        d = [(1, i, 0, 0, i == 0, i == N - 1) for i in range(N)]
        dut.dataIn._ag.data.extend(d)
        self.randomize(dut.dataIn)
        self.randomize(dut.dataOut)

        self.runSim(4 * N * self.CLK)

        self.assertValSequenceEqual(
            dut.dataOut._ag.data,
            d
        )


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AvalonStAgentTC("test_passdata")])
    suite = testLoader.loadTestsFromTestCase(AvalonStAgentTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
