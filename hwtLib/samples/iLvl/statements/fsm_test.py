#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwt.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.statements.fsm import FsmExample, HadrcodedFsmExample


class FsmExampleTC(unittest.TestCase):
    def setUp(self):
        u = FsmExample()
        self.u, self.model, self.procs = simPrepare(u)
        
    def runSim(self, name, time=80 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/fsmExample_%s.vcd" % name,
                time=time)
            
    def test_allCases(self):
        u = self.u
        
        u.a._ag.data = [1, 1, 1, 0, 0, 0, 0, 0]
        u.b._ag.data = [0, 1, 0, 0, 1, 0, 1, 0] 
        
        self.runSim("allCases")
        
        self.assertSequenceEqual([1, 1, 3, 1, 1, 2, 2, 2], agInts(u.dout))

class HadrcodedFsmExampleTC(FsmExampleTC):
    def setUp(self):
        u = HadrcodedFsmExample()
        self.u, self.model, self.procs = simPrepare(u)

    def runSim(self, name, time=80 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/hadrcodedFsmExample_%s.vcd" % name,
                time=time)

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(FsmExampleTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
