#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import WRITE, READ, Time
from hwt.simulator.agentConnector import valuesToInts
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.ram import Ram_sp


class RamTC(SimTestCase):

    def test_writeAndRead(self):
        u = Ram_sp()
        u.DATA_WIDTH.set(8)
        u.ADDR_WIDTH.set(3)
        self.prepareUnit(u)

        u.a._ag.requests.extend([(WRITE, 0, 5), (WRITE, 1, 7),
                                 (READ, 0), (READ, 1),
                                 (READ, 0), (READ, 1), (READ, 2)])

        self.runSim(110 * Time.ns)
        self.assertSequenceEqual(valuesToInts(self.model.ram_memory._val),
                                 [5, 7, None, None, None, None, None, None])
        self.assertSequenceEqual(valuesToInts(u.a._ag.readed),
                                 [5, 7, 5, 7, None])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(RamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
