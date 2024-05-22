#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import Time, NOP
from hwt.hwIOs.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.simpleHwModuleAxi4Stream import SimpleHwModuleAxi4Stream
from pyMathBitPrecise.bit_utils import mask


class SynchronizedSimpleHwModuleAxi4Stream(SimpleHwModuleAxi4Stream):
    """
    :class:`hwt.hwModule.HwModule` with reference clk added
    """

    def _declr(self):
        SimpleHwModuleAxi4Stream._declr(self)
        addClkRstn(self)


class SimpleModuleAxi4Stream_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = SynchronizedSimpleHwModuleAxi4Stream()
        cls.compileSim(cls.dut)

    def test_nop(self):
        dut = self.dut
        self.runSim(200 * Time.ns)

        self.assertEqual(len(dut.b._ag.data), 0)

    def test_pass(self):
        dut = self.dut

        dut.a._ag.data.extend([(11, mask(dut.a.strb._dtype.bit_length()), 1),
                             NOP,
                             (12, mask(dut.a.strb._dtype.bit_length()), 1)
                             ])

        self.runSim(200 * Time.ns)
        self.assertEqual(len(dut.b._ag.data), 2)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([SimpleModuleAxi4Stream_TC("test_nop")])
    suite = testLoader.loadTestsFromTestCase(SimpleModuleAxi4Stream_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
