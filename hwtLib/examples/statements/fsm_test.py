#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.statements.fsm import FsmExample, HadrcodedFsmExample


class FsmExampleTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = FsmExample()
        cls.compileSim(cls.dut)

    def test_allCases(self):
        dut = self.dut

        dut.a._ag.data.extend([1, 1, 1, 0, 0, 0, 0, 0])
        dut.b._ag.data.extend([0, 1, 0, 0, 1, 0, 1, 0])

        self.runSim(90 * Time.ns)

        self.assertValSequenceEqual(dut.dout._ag.data,
                                    [1, 1, 3, 1, 1, 2, 2, 2])


class HadrcodedFsmExampleTC(FsmExampleTC):

    @classmethod
    def setUpClass(cls):
        cls.dut = HadrcodedFsmExample()
        cls.compileSim(cls.dut)


class FsmSerializationTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_vhdl(self):
        self.assert_serializes_as_file(FsmExample, "FsmExample.vhd")

    def test_verilog(self):
        self.assert_serializes_as_file(FsmExample, "FsmExample.v")

    def test_systemc(self):
        self.assert_serializes_as_file(FsmExample, "FsmExample.cpp")


if __name__ == "__main__":
    _ALL_TCs = [FsmExampleTC, HadrcodedFsmExampleTC, FsmSerializationTC]
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([FsmExampleTC("test_nothingEnable")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
