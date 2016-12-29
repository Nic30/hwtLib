#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwt.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.statements.ifStm import SimpleIfStatement


class IfStmTC(unittest.TestCase):
    def setUp(self):
        u = SimpleIfStatement()
        self.u, self.model, self.procs = simPrepare(u)
        
    def runSim(self, name, time=80 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/ifStm_%s.vcd" % name,
                time=time)
            
    def test_allCases(self):
        u = self.u
        
        u.a._ag.data = [1, 1, 1, 0, 0, 0, 0, 0]
        u.b._ag.data = [0, 1, None, 0, 1, None, 1, 0] 
        u.c._ag.data = [0, 0, 0, 0, 1, 0, 0, 0]
        
        self.runSim("allCases")
        
        self.assertSequenceEqual([0, 1, None, 0, 1, None, 0, 0], agInts(u.d))

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(IfStmTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
