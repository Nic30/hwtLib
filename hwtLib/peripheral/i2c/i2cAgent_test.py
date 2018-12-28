#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SimpleSimTestCase
from hwt.synthesizer.unit import Unit
from hwtLib.peripheral.i2c.intf import I2c, I2cAgent
from pycocotb.constants import CLK_PERIOD


class I2CSimplePassTrought(Unit):
    def _declr(self):
        self.i = I2c()
        self.o = I2c()._m()

    def _impl(self):
        self.o(self.i)


class I2cAgent_TC(SimpleSimTestCase):
    @classmethod
    def getUnit(cls):
        cls.u = I2CSimplePassTrought()
        return cls.u

    def setUp(self):
        SimpleSimTestCase.setUp(self)
        self.u.o._ag.sda.pullMode = None
        self.u.o._ag.scl.pullMode = None

    def test_nop(self):
        u = self.u
        ref = [0]
        u.i._ag.bits.extend(ref)

        self.runSim(10 * CLK_PERIOD)
        self.assertValSequenceEqual(u.o._ag.bits,
                                    [I2cAgent.START] + [0 for _ in range(10)])

    def test_simple(self):
        u = self.u

        ref = [1, 0, 0, 1, 1, 1, 0, 1, 0]
        expected = [I2cAgent.START, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0]
        u.i._ag.bits.extend(ref)

        self.runSim(10 * CLK_PERIOD)
        self.assertValSequenceEqual(u.o._ag.bits,
                                    expected)


if __name__ == "__main__":
    # from hwt.synthesizer.utils import toRtl
    # print(toRtl(I2CSimplePassTrought()))
    suite = unittest.TestSuite()
    suite.addTest(I2cAgent_TC('test_simple'))
    # suite.addTest(unittest.makeSuite(I2cAgent_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
