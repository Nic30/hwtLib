#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceRAM
from hwt.simulator.agentConnector import agInts, valuesToInts
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.utils import toRtl
from hwtLib.samples.mem.ram import SimpleAsyncRam, SimpleSyncRam


class RamTC(SimTestCase):
    def setUpAsync(self):
        self.setUp()
        self.u = SimpleAsyncRam()
        self.prepareUnit(self.u)

    def setUpSync(self):
        self.setUp()
        self.u = SimpleSyncRam()
        self.prepareUnit(self.u)

    def test_async_allData(self):
        self.setUpAsync()
        u = self.u

        u.addr_in._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])
        u.addr_out._ag.data.extend([None, 0, 1, 2, 3, None, 0, 1])
        u.din._ag.data.extend([10, 11, 12, 13, 14, 15, 16, 17])
        self.runSim(80 * Time.ns)

        self.assertSequenceEqual(valuesToInts([v for v in self.model.ram_data._val]),
                                 [None, 17, 16, 15])
        self.assertSequenceEqual(agInts(u.dout),
                                 [None, 10, 11, 12, None, None, None, 17])

    def test_sync_allData(self):
        self.setUpSync()
        u = self.u

        u.addr_in._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])
        u.addr_out._ag.data.extend([None, 0, 1, 2, 3, None, 0, 1])
        u.din._ag.data.extend([10, 11, 12, 13, 14, 15, 16, 17])
        self.runSim(80 * Time.ns)

        self.assertSequenceEqual(valuesToInts([v for v in self.model.ram_data._val]),
                                 [None, 17, 16, 15])
        self.assertSequenceEqual(agInts(u.dout),
                                 [None, None, 10, 11, 12, 13, None, None])

    def test_async_resources(self):
        u = SimpleAsyncRam()
        expected = {
            ResourceRAM(8, 4,
                        0, 0, 0, 0,
                        0, 1, 1, 0): 1,
        }

        s = ResourceAnalyzer()
        toRtl(u, serializer=s)
        self.assertDictEqual(s.report(), expected)

    def test_sync_resources(self):
        u = SimpleSyncRam()
        expected = {
            ResourceRAM(8, 4,
                        0, 1, 1, 0,
                        0, 0, 0, 0): 1,
        }

        s = ResourceAnalyzer()
        toRtl(u, serializer=s)
        self.assertDictEqual(s.report(), expected)

if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(RamTC('test_async_resources'))
    suite.addTest(unittest.makeSuite(RamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
