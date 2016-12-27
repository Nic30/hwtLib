#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwt.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.arithmetic.selfRefCntr import SelfRefCntr


class SelfRefCntrTC(unittest.TestCase):
    def setUp(self):
        self.u, self.model, self.procs = simPrepare(SelfRefCntr())
        
    def runSim(self, name, time=90 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/selfRefCntr_%s.vcd" % name,
                time=90 * Time.ns)
    
    def test_overflow(self):
        u = self.u
        
        self.runSim("overflow")
        self.assertSequenceEqual([0, 0, 1, 2, 3, 4, 0, 1, 2], agInts(u.dout))
       
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(SelfRefCntrTC('test_overflow'))
    suite.addTest(unittest.makeSuite(SelfRefCntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
