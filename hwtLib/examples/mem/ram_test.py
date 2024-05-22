#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.case import TestCase

from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceRAM
from hwt.simulator.simTestCase import SimTestCase
from hwt.synth import synthesised
from hwtLib.examples.mem.ram import SimpleAsyncRam, SimpleSyncRam
from hwtSimApi.constants import CLK_PERIOD


class SimpleAsyncRamTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = SimpleAsyncRam()
        cls.compileSim(cls.dut)

    def test_async_allData(self):
        dut = self.dut

        dut.addr_in._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])
        dut.addr_out._ag.data.extend([None, 0, 1, 2, 3, None, 0, 1])
        dut.din._ag.data.extend([10, 11, 12, 13, 14, 15, 16, 17])
        self.runSim(8 * CLK_PERIOD)

        ae = self.assertValSequenceEqual
        ram = self.rtl_simulator.model.io.ram_data
        ae([x.read() for x in ram], [None, 17, 16, 15])
        ae(dut.dout._ag.data, [None, 10, 11, 12, None, None, None, 17])


class SimpleSyncRamTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = SimpleSyncRam()
        cls.compileSim(cls.dut)

    def test_sync_allData(self):
        dut = self.dut

        dut.addr_in._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])
        dut.addr_out._ag.data.extend([None, 0, 1, 2, 3, None, 0, 1])
        dut.din._ag.data.extend([10, 11, 12, 13, 14, 15, 16, 17])
        self.runSim(8 * CLK_PERIOD)

        ae = self.assertValSequenceEqual
        ram = self.rtl_simulator.model.io.ram_data
        ae([x.read() for x in ram], [None, 17, 16, 15])
        ae(dut.dout._ag.data, [None, None, 10, 11, 12, 13, None, None])


class RamResourcesTC(TestCase):

    def test_async_resources(self):
        m = SimpleAsyncRam()
        expected = {
            ResourceRAM(8, 4,
                        0, 0, 0, 0,
                        0, 1, 1, 0): 1,
        }

        s = ResourceAnalyzer()
        synthesised(m)
        s.visit_HwModule(m)
        self.assertDictEqual(s.report(), expected)

    def test_sync_resources(self):
        m = SimpleSyncRam()
        expected = {
            ResourceRAM(8, 4,
                        0, 1, 1, 0,
                        0, 0, 0, 0): 1,
        }

        s = ResourceAnalyzer()
        synthesised(m)
        s.visit_HwModule(m)
        self.assertDictEqual(s.report(), expected)


if __name__ == "__main__":
    _ALL_TCs = [RamResourcesTC, SimpleAsyncRamTC, SimpleSyncRamTC]

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([RamResourcesTC("test_async_resources")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
