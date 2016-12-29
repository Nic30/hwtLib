#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwt.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.statements.switchStm import SwitchStmUnit


class SwitchStmTC(unittest.TestCase):
    def setUp(self):
        u = SwitchStmUnit()
        self.u, self.model, self.procs = simPrepare(u)

    def runSim(self, name, time=200 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/switchStm_%s.vcd" % name,
                time=time)
            
    def test_allCases(self):
        u = self.u
        u.sel._ag.data = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 1]
        u.b._ag.data = [0, 1, 0, 0, 0, 0, 0, 0, 1, None, 0] 
        u.c._ag.data = [0, 0, 0, 1, 0, 0, 0, 0, 1, None, 0]
        u.d._ag.data = [0, 0, 0, 0, 0, 1, 0, 0, 1, None, 0]
        
        self.runSim("allCases")
        
        self.assertSequenceEqual([0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0], agInts(u.a))

        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(SwitchStmTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
