#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.unit import Unit

from hwtLib.avalon.st import AvalonST
from pycocotb.constants import CLK_PERIOD


class AvalonStWire(Unit):

    def _declr(self):
        addClkRstn(self)
        self.dataIn = AvalonST()
        self.dataOut = AvalonST()._m()

    def _impl(self):
        self.dataOut(self.dataIn)


class AvalonStAgentTC(SingleUnitSimTestCase):
    CLK = CLK_PERIOD

    @classmethod
    def getUnit(cls):
        u = AvalonStWire()
        return u

    def test_nop(self):
        u = self.u
        self.runSim(CLK_PERIOD)

        self.assertValSequenceEqual(
            u.dataOut._ag.data,
            []
        )

    def test_can_pass_data(self):
        u = self.u
        N = 10

        #channel, data, error, startOfPacket, endOfPacket
        d = [(1, i, 0, i == 0, i == N - 1) for i in range(N)]
        u.dataIn._ag.data.extend(d)

        self.runSim((N + 10) * self.CLK)

        self.assertValSequenceEqual(
            u.dataOut._ag.data,
            d
        )

    def test_can_pass_data_randomized(self):
        u = self.u
        N = 40

        #channel, data, error, startOfPacket, endOfPacket
        d = [(1, i, 0, i == 0, i == N - 1) for i in range(N)]
        u.dataIn._ag.data.extend(d)
        self.randomize(u.dataIn)
        self.randomize(u.dataOut)

        self.runSim(4 * N * self.CLK)

        self.assertValSequenceEqual(
            u.dataOut._ag.data,
            d
        )


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HsFifoTC('test_passdata'))
    suite.addTest(unittest.makeSuite(AvalonStAgentTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
