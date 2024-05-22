#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.operatorDefs import HwtOps
from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceMUX, \
    ResourceFF
from hwt.simulator.simTestCase import SimTestCase
from hwt.synth import synthesised
from hwtLib.examples.arithmetic.cntr import Cntr
from hwtSimApi.constants import CLK_PERIOD


class CntrTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = Cntr()
        cls.compileSim(cls.dut)

    def test_overflow(self):
        dut = self.dut

        dut.en._ag.data.append(1)
        self.runSim(9 * CLK_PERIOD)
        self.assertValSequenceEqual(dut.val._ag.data,
                                    [0, 1, 2, 3, 0, 1, 2, 3])

    def test_contingWithStops(self):
        dut = self.dut

        dut.en._ag.data.extend([1, 0, 1, 1, 0, 0, 0])
        self.runSim(9 * CLK_PERIOD)
        self.assertValSequenceEqual(dut.val._ag.data,
                                    [0, 1, 1, 2, 3, 3, 3, 3])


class CntrResourceAnalysisTC(unittest.TestCase):

    def test_resources_2b(self):
        dut = Cntr()

        expected = {(HwtOps.ADD, 2): 1,
                    # 1 for reset, one for en
                    (ResourceMUX, 2, 2): 2,
                    ResourceFF: 2}

        s = ResourceAnalyzer()
        synthesised(dut)
        s.visit_HwModule(dut)
        r = s.report()
        self.assertDictEqual(r, expected)

    def test_resources_150b(self):
        dut = Cntr()
        dut.DATA_WIDTH = 150

        expected = {(HwtOps.ADD, 150): 1,
                    # 1 for reset, one for en
                    (ResourceMUX, 150, 2): 2,
                    ResourceFF: 150}

        s = ResourceAnalyzer()
        synthesised(dut)
        s.visit_HwModule(dut)
        r = s.report()
        self.assertDictEqual(r, expected)


if __name__ == "__main__":
    ALL_TCs = [CntrTC, CntrResourceAnalysisTC]
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([CntrTC("test_overflow")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
