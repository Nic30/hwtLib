#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.case import TestCase

from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceRAM
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.utils import toRtl
from hwtLib.examples.mem.rom import SimpleRom, SimpleSyncRom
from pycocotb.constants import CLK_PERIOD


class SimpleRomTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = SimpleRom()
        return cls.u

    def test_async_allData(self):
        u = self.u

        u.addr._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])

        self.runSim(8 * CLK_PERIOD)

        self.assertValSequenceEqual(
            u.dout._ag.data, [1, 2, 3, 4, None, 4, 3, 2])


class SimpleSyncRomTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = SimpleSyncRom()
        return cls.u

    def test_sync_allData(self):
        u = self.u

        u.addr._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])

        self.runSim(9 * CLK_PERIOD)

        self.assertValSequenceEqual(
            u.dout._ag.data, [None, 1, 2, 3, 4, None, 4, 3, 2])


class RomResourcesTC(TestCase):

    def test_sync_resources(self):
        u = SimpleSyncRom()
        expected = {
            ResourceRAM(8, 4,
                        0, 1, 0, 0,
                        0, 0, 0, 0): 1,
        }

        s = ResourceAnalyzer()
        toRtl(u, serializer=s)
        self.assertDictEqual(s.report(), expected)

    def test_async_resources(self):
        u = SimpleRom()
        expected = {
            ResourceRAM(8, 4,
                        0, 0, 0, 0,
                        0, 1, 0, 0): 1,
        }

        s = ResourceAnalyzer()
        toRtl(u, serializer=s)
        r = s.report()
        self.assertDictEqual(r, expected)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(RomTC('test_sync_resources'))
    suite.addTest(unittest.makeSuite(SimpleRomTC))
    suite.addTest(unittest.makeSuite(SimpleSyncRomTC))
    suite.addTest(unittest.makeSuite(RomResourcesTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
