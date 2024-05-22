#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.case import TestCase

from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceRAM
from hwt.simulator.simTestCase import SimTestCase
from hwt.synth import synthesised
from hwtLib.examples.mem.rom import SimpleRom, SimpleSyncRom
from hwtSimApi.constants import CLK_PERIOD


class SimpleRomTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = SimpleRom()
        cls.compileSim(cls.dut)

    def test_async_allData(self):
        dut = self.dut

        dut.addr._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])

        self.runSim(8 * CLK_PERIOD)

        self.assertValSequenceEqual(
            dut.dout._ag.data, [1, 2, 3, 4, None, 4, 3, 2])


class SimpleSyncRomTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = SimpleSyncRom()
        cls.compileSim(cls.dut)

    def test_sync_allData(self):
        dut = self.dut

        dut.addr._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])

        self.runSim(9 * CLK_PERIOD)

        self.assertValSequenceEqual(
            dut.dout._ag.data, [None, 1, 2, 3, 4, None, 4, 3, 2])


class RomResourcesTC(TestCase):

    def test_sync_resources(self):
        m = SimpleSyncRom()
        expected = {
            ResourceRAM(8, 4,
                        0, 1, 0, 0,
                        0, 0, 0, 0): 1,
        }

        s = ResourceAnalyzer()
        synthesised(m)
        s.visit_HwModule(m)
        self.assertDictEqual(s.report(), expected)

    def test_async_resources(self):
        m = SimpleRom()
        expected = {
            ResourceRAM(8, 4,
                        0, 0, 0, 0,
                        0, 1, 0, 0): 1,
        }

        s = ResourceAnalyzer()
        synthesised(m)
        s.visit_HwModule(m)
        r = s.report()
        self.assertDictEqual(r, expected)


if __name__ == "__main__":
    _ALL_TCs = [SimpleRomTC, SimpleSyncRomTC, RomResourcesTC]

    testLoader = unittest.TestLoader()
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
