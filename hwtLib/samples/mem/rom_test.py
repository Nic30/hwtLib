#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.mem.rom import SimpleRom, SimpleSyncRom


class RomTC(SimTestCase):

    def test_async_allData(self):
        u = SimpleRom()
        self.prepareUnit(u)

        u.addr._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])

        self.doSim(80 * Time.ns)

        self.assertValSequenceEqual(u.dout._ag.data, [1, 2, 3, 4, None, 4, 3, 2])

    def test_sync_allData(self):
        u = SimpleSyncRom()
        self.prepareUnit(u)

        u.addr._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])

        self.doSim(90 * Time.ns)

        self.assertValSequenceEqual(u.dout._ag.data, [None, 1, 2, 3, 4, None, 4, 3, 2])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(RomTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
