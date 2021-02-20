#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.statements.fsm import FsmExample, HadrcodedFsmExample


class FsmExampleTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = FsmExample()
        cls.compileSim(cls.u)

    def test_allCases(self):
        u = self.u

        u.a._ag.data.extend([1, 1, 1, 0, 0, 0, 0, 0])
        u.b._ag.data.extend([0, 1, 0, 0, 1, 0, 1, 0])

        self.runSim(90 * Time.ns)

        self.assertValSequenceEqual(u.dout._ag.data,
                                    [1, 1, 3, 1, 1, 2, 2, 2])


class HadrcodedFsmExampleTC(FsmExampleTC):

    @classmethod
    def setUpClass(cls):
        cls.u = HadrcodedFsmExample()
        cls.compileSim(cls.u)


class FsmSerializationTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_vhdl(self):
        self.assert_serializes_as_file(FsmExample, "FsmExample.vhd")

    def test_verilog(self):
        self.assert_serializes_as_file(FsmExample, "FsmExample.v")

    def test_systemc(self):
        self.assert_serializes_as_file(FsmExample, "FsmExample.cpp")


if __name__ == "__main__":

    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(FsmExampleTC))
    suite.addTest(unittest.makeSuite(HadrcodedFsmExampleTC))
    suite.addTest(unittest.makeSuite(FsmSerializationTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
