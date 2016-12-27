#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwt.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.arithmetic.cntr import Cntr


class CntrTC(unittest.TestCase):
    def setUp(self):
        self.u, self.model, self.procs = simPrepare(Cntr())
        
    def runSim(self, name, time=90 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/cntr_%s.vcd" % name,
                time=90 * Time.ns)
    
    def test_overflow(self):
        u = self.u
        
        u.en._ag.data = [1]
        self.runSim("overflow")
        self.assertSequenceEqual([0, 0, 1, 2, 3, 0, 1, 2, 3], agInts(u.val))


    def test_contingWithStops(self):
        u = self.u
        
        u.en._ag.data = [1, 0, 1, 1, 0, 0, 0]
        self.runSim("contingWithStops")
        self.assertSequenceEqual([0, 0, 0, 1, 2, 2, 2, 2, 2], agInts(u.val))

    
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(CntrTC('test_overflow'))
    suite.addTest(unittest.makeSuite(CntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
