#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.handshaked.splitCopy import HsSplitCopy
from pycocotb.constants import CLK_PERIOD


class HsSplitCopyWithReference(HsSplitCopy):
    def _declr(self):
        HsSplitCopy._declr(self)
        addClkRstn(self)


class HsSplitCopyTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = HsSplitCopyWithReference(Handshaked)
        cls.u.DATA_WIDTH = 4
        return cls.u

    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])

        self.runSim(15 * CLK_PERIOD)

        aeq = self.assertValSequenceEqual
        aeq(u.dataOut[0]._ag.data, [1, 2, 3, 4, 5, 6])
        aeq(u.dataOut[1]._ag.data, [1, 2, 3, 4, 5, 6])

        aeq([], u.dataIn._ag.data)


class HsSplitCopy_randomized_TC(HsSplitCopyTC):
    def setUp(self):
        super(HsSplitCopy_randomized_TC, self).setUp()
        self.randomize(self.u.dataIn)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(HsSplitCopy_randomized_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
