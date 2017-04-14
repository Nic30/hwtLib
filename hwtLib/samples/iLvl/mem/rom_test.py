#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.iLvl.mem.rom import SimpleRom


class RomTC(SimTestCase):
    def setUp(self):
        super(RomTC, self).setUp()
        self.u = SimpleRom()
        self.prepareUnit(self.u)

    def test_allData(self):
        u = self.u

        u.addr._ag.data = [0, 1, 2, 3, None, 3, 2, 1]

        self.doSim(80 * Time.ns)

        self.assertSequenceEqual([1, 2, 3, 4, None, 4, 3, 2], agInts(u.dout))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(RomTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
