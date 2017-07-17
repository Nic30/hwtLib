#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.splitCopy import HsSplitCopy


class HsSplitCopyWithReference(HsSplitCopy):
    def _declr(self):
        HsSplitCopy._declr(self)
        addClkRstn(self)


class HsSplitCopyTC(SimTestCase):
    def setUp(self):
        super(HsSplitCopyTC, self).setUp()
        self.u = HsSplitCopyWithReference(Handshaked)
        self.u.DATA_WIDTH.set(4)
        self.prepareUnit(self.u)

    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])

        self.doSim(150 * Time.ns)

        self.assertValSequenceEqual(u.dataOut[0]._ag.data, [1, 2, 3, 4, 5, 6])
        self.assertValSequenceEqual(u.dataOut[1]._ag.data, [1, 2, 3, 4, 5, 6])

        self.assertSequenceEqual([], u.dataIn._ag.data)


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
