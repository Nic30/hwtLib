#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import WRITE, READ, Time
from hwt.simulator.agentConnector import valuesToInts
from hwt.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.mem.ram import Ram_sp


class RamTC(unittest.TestCase):

    def test_writeAndRead(self):
        u = Ram_sp()
        u.DATA_WIDTH.set(8)
        u.ADDR_WIDTH.set(3)
        u, model, procs = simPrepare(u)

        u.a._ag.requests = [(WRITE, 0, 5), (WRITE, 1, 7),
                            (READ, 0), (READ, 1),
                            (READ, 0), (READ, 1), (READ, 2)] 
        
        
        simUnitVcd(model, procs,
                   "tmp/ram_writeAndRead.vcd", time=110 * Time.ns)
        self.assertSequenceEqual([5, 7, None, None, None, None, None, None],
                                  valuesToInts(model.ram_memory._val.val))
        self.assertSequenceEqual([5, 7, 5, 7, None],
                                 valuesToInts(u.a._ag.readed))

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(RamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
