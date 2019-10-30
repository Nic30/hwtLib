#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.unit import Unit

from hwtLib.avalon.mm import AvalonMM
from pycocotb.constants import CLK_PERIOD


class AvalonMmWire(Unit):

    def _declr(self):
        addClkRstn(self)
        self.dataIn = AvalonMM()
        self.dataOut = AvalonMM()._m()

    def _impl(self):
        self.dataOut(self.dataIn)


class AvalonMmAgentTC(SingleUnitSimTestCase):
    CLK = CLK_PERIOD

    @classmethod
    def getUnit(cls):
        cls.u = AvalonMmWire()
        return cls.u

    def test_nop(self):
        u = self.u
        self.runSim(10 * self.CLK)

        self.assertEmpty(u.dataOut._ag.req)
        self.assertEmpty(u.dataOut._ag.wData)
        self.assertEmpty(u.dataIn._ag.rData)
        self.assertEmpty(u.dataIn._ag.wResp)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(HsFifoTC('test_passdata'))
    suite.addTest(unittest.makeSuite(AvalonMmAgentTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
