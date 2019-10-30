#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.logic.oneHotToBin import OneHotToBin
from pycocotb.constants import CLK_PERIOD


class OneHotToBinSimWrap(OneHotToBin):

    def _declr(self):
        OneHotToBin._declr(self)
        addClkRstn(self)


class OneHotToBinTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = OneHotToBinSimWrap()
        cls.ONE_HOT_WIDTH = 8
        u.ONE_HOT_WIDTH = cls.ONE_HOT_WIDTH
        return u

    def test_nop(self):
        u = self.u
        oneHot = u.oneHot._ag.data
        oneHot.append(0)

        self.runSim(4 * CLK_PERIOD)

        self.assertValSequenceEqual(u.bin._ag.data, [])

    def test_basic(self):
        u = self.u
        oneHot = u.oneHot._ag.data
        oneHot.append(0)
        for i in range(self.ONE_HOT_WIDTH):
            oneHot.append(1 << i)
        oneHot.append(0)

        self.runSim((self.ONE_HOT_WIDTH + 3) * CLK_PERIOD)

        self.assertValSequenceEqual(u.bin._ag.data, range(self.ONE_HOT_WIDTH))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(OneHotToBinTC('test_basic'))
    suite.addTest(unittest.makeSuite(OneHotToBinTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
