#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hwIOs.std import HwIODataRdVld
from hwt.hwIOs.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.splitCopy import HsSplitCopy
from hwtSimApi.constants import CLK_PERIOD


class HsSplitCopyWithReference(HsSplitCopy):
    def _declr(self):
        HsSplitCopy._declr(self)
        addClkRstn(self)


class HsSplitCopyTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = HsSplitCopyWithReference(HwIODataRdVld)
        cls.dut.DATA_WIDTH = 4
        cls.compileSim(cls.dut)

    def test_passdata(self):
        dut = self.dut
        dut.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])

        self.runSim(15 * CLK_PERIOD)

        aeq = self.assertValSequenceEqual
        aeq(dut.dataOut[0]._ag.data, [1, 2, 3, 4, 5, 6])
        aeq(dut.dataOut[1]._ag.data, [1, 2, 3, 4, 5, 6])

        aeq([], dut.dataIn._ag.data)


class HsSplitCopy_randomized_TC(HsSplitCopyTC):
    def setUp(self):
        super(HsSplitCopy_randomized_TC, self).setUp()
        self.randomize(self.dut.dataIn)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HsSplitCopy_randomized_TC("test_normalOp")])
    suite = testLoader.loadTestsFromTestCase(HsSplitCopy_randomized_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
