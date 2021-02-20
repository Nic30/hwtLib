#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.case import TestCase

from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceRAM
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.utils import synthesised
from hwtLib.examples.mem.ram import SimpleAsyncRam, SimpleSyncRam
from hwtSimApi.constants import CLK_PERIOD


class SimpleAsyncRamTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = SimpleAsyncRam()
        cls.compileSim(cls.u)

    def test_async_allData(self):
        u = self.u

        u.addr_in._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])
        u.addr_out._ag.data.extend([None, 0, 1, 2, 3, None, 0, 1])
        u.din._ag.data.extend([10, 11, 12, 13, 14, 15, 16, 17])
        self.runSim(8 * CLK_PERIOD)

        ae = self.assertValSequenceEqual
        ram = self.rtl_simulator.model.io.ram_data
        ae([x.read() for x in ram], [None, 17, 16, 15])
        ae(u.dout._ag.data, [None, 10, 11, 12, None, None, None, 17])


class SimpleSyncRamTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = SimpleSyncRam()
        cls.compileSim(cls.u)

    def test_sync_allData(self):
        u = self.u

        u.addr_in._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])
        u.addr_out._ag.data.extend([None, 0, 1, 2, 3, None, 0, 1])
        u.din._ag.data.extend([10, 11, 12, 13, 14, 15, 16, 17])
        self.runSim(8 * CLK_PERIOD)

        ae = self.assertValSequenceEqual
        ram = self.rtl_simulator.model.io.ram_data
        ae([x.read() for x in ram], [None, 17, 16, 15])
        ae(u.dout._ag.data, [None, None, 10, 11, 12, 13, None, None])


class RamResourcesTC(TestCase):

    def test_async_resources(self):
        u = SimpleAsyncRam()
        expected = {
            ResourceRAM(8, 4,
                        0, 0, 0, 0,
                        0, 1, 1, 0): 1,
        }

        s = ResourceAnalyzer()
        synthesised(u)
        s.visit_Unit(u)
        self.assertDictEqual(s.report(), expected)

    def test_sync_resources(self):
        u = SimpleSyncRam()
        expected = {
            ResourceRAM(8, 4,
                        0, 1, 1, 0,
                        0, 0, 0, 0): 1,
        }

        s = ResourceAnalyzer()
        synthesised(u)
        s.visit_Unit(u)
        self.assertDictEqual(s.report(), expected)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(RamTC('test_async_resources'))
    suite.addTest(unittest.makeSuite(RamResourcesTC))
    suite.addTest(unittest.makeSuite(SimpleAsyncRamTC))
    suite.addTest(unittest.makeSuite(SimpleSyncRamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
