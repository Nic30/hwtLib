#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts, valuesToInts
from hwtLib.samples.iLvl.mem.ram import SimpleAsyncRam, SimpleSyncRam
from hwt.simulator.simTestCase import SimTestCase


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

        u.addr_in._ag.data = [0, 1, 2, 3, None, 3, 2, 1]
        u.addr_out._ag.data = [None, 0, 1, 2, 3, None, 0, 1]
        u.din._ag.data = [10, 11, 12, 13, 14, 15, 16, 17]
        self.doSim(80 * Time.ns)

        self.assertSequenceEqual(valuesToInts(self.model.ram_data._val.val), [None, 17, 16, 15])
        self.assertSequenceEqual(agInts(u.dout), [None, 10, 11, 12, None, None, None, 17])

    def test_sync_allData(self):
        self.setUpSync()
        u = self.u

        u.addr_in._ag.data = [0, 1, 2, 3, None, 3, 2, 1]
        u.addr_out._ag.data = [None, 0, 1, 2, 3, None, 0, 1]
        u.din._ag.data = [10, 11, 12, 13, 14, 15, 16, 17]
        self.doSim(80 * Time.ns)

        self.assertSequenceEqual(valuesToInts(self.model.ram_data._val.val), [None, 17, 16, 15])
        self.assertSequenceEqual(agInts(u.dout), [None, None, 10, 11, 12, 13, None, None])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(RamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
