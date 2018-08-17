#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit

from hwtLib.avalon.st import AvalonST


class AvalonStWire(Unit):

    def _declr(self):
        addClkRstn(self)
        self.dataIn = AvalonST()
        self.dataOut = AvalonST()

    def _impl(self):
        self.dataOut(self.dataIn)


class AvalonStAgentTC(SimTestCase):
    CLK = 10 * Time.ns

    def setUp(self):
        SimTestCase.setUp(self)
        self.u = AvalonStWire()
        self.prepareUnit(self.u)

    def test_nop(self):
        u = self.u
        self.runSim(10 * self.CLK)

        self.assertValSequenceEqual(
            u.dataOut._ag.data,
            []
        )

    def test_can_pass_data(self):
        u = self.u
        N = 10

        u.dataIn._ag.data.extend(range(N))

        self.runSim((N + 10) * self.CLK)

        self.assertValSequenceEqual(
            u.dataOut._ag.data,
            range(N)
        )

    def test_can_pass_data_randomized(self):
        u = self.u
        N = 40

        u.dataIn._ag.data.extend(range(N))
        self.randomize(u.dataIn)
        self.randomize(u.dataOut)

        self.runSim(4 * N * self.CLK)

        self.assertValSequenceEqual(
            u.dataOut._ag.data,
            range(N)
        )


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HsFifoTC('test_passdata'))
    suite.addTest(unittest.makeSuite(AvalonStAgentTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
