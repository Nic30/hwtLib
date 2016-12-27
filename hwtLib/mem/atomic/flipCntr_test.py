#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time, NOP
from hwt.simulator.agentConnector import valuesToInts
from hwt.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.mem.atomic.flipCntr import FlipCntr


class FlipCntrTC(unittest.TestCase):
    def setUp(self):
        self.u, self.model, self.procs = simPrepare(FlipCntr())
        
    def runSim(self, name, time=90 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/flipCntr_%s.vcd" % name,
                time=90 * Time.ns)
    
    def test_nop(self):
        u = self.u
        
        u.doIncr._ag.data = [0, 0]
        self.runSim("nop")
    
        self.assertSequenceEqual([0 for _ in range(9)], valuesToInts(u.data._ag.din))
    
    def test_incr(self):
        u = self.u
        
        u.doIncr._ag.data = [0, 0, 1, 0, 0, 0]
        u.doFlip._ag.data = [NOP, NOP, NOP, 1, NOP, NOP]
        
        self.runSim("incr")
    
        self.assertSequenceEqual([0, 0, 0, 0] + [1 for _ in range(5)], valuesToInts(u.data._ag.din))
    
        
    
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(FlipCntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
