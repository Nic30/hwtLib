#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwt.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.operators.indexing import (SimpleIndexingSplit,
                                                    SimpleIndexingJoin,
                                                    SimpleIndexingRangeJoin,
                                                    IndexingInernSplit,
                                                    IndexingInernJoin)


class IndexingTC(unittest.TestCase):
    def setUpUnit(self, unit):
        self.u, self.model, self.procs = simPrepare(unit)
    
    def runSim(self, name, time=80 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/indexing_%s.vcd" % name,
                time=time)
            
    def test_split(self):
        u = SimpleIndexingSplit()
        self.setUpUnit(u)
        
        u.a._ag.data = [0, 1, 2, 3, None, 3, 2, 1]
        
        self.runSim("split")
        
        self.assertSequenceEqual([0, 1, 0, 1, None, 1, 0, 1], agInts(u.b))
        self.assertSequenceEqual([0, 0, 1, 1, None, 1, 1, 0], agInts(u.c))

    def test_join(self):
        u = SimpleIndexingJoin()
        self.setUpUnit(u)
        
        u.b._ag.data = [0, 1, 0, 1, None, 1, 0, 1]
        u.c._ag.data = [0, 0, 1, 1, None, 1, 1, 0]
        
        self.runSim("join")
        
        self.assertSequenceEqual([0, 1, 2, 3, None, 3, 2, 1], agInts(u.a))
        
    def test_rangeJoin(self):
        u = SimpleIndexingRangeJoin()
        self.setUpUnit(u)
        
        u.b._ag.data = [0, 3, 0, 3, None, 3, 0, 3]
        u.c._ag.data = [0, 0, 3, 3, None, 3, 3, 0]
        
        self.runSim("rangeJoin")
        
        self.assertSequenceEqual([0, 3, 12, 15, None, 15, 12, 3], agInts(u.a))
        
    def test_internSplit(self):
        u = IndexingInernSplit()
        self.setUpUnit(u)
        
        u.a._ag.data = [0, 1, 2, 3, None, 3, 0, 3]
        
        self.runSim("internSplit")
        
        self.assertSequenceEqual([0, 1, 2, 3, None, 3, 0, 3], agInts(u.b))
    
    def test_internJoin(self):
        u = IndexingInernJoin()
        self.setUpUnit(u)
        
        u.a._ag.data = [0, 1, 0, 1, None, 0, 1, 0]
        u.b._ag.data = [0, 0, 1, 1, None, 0, 1, 0]
        
        
        self.runSim("internJoin")
        
        self.assertSequenceEqual([0, 1, 0, 1, None, 0, 1, 0], agInts(u.c))
        self.assertSequenceEqual([0, 0, 1, 1, None, 0, 1, 0], agInts(u.d))
        
        
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(IndexingTC('test_split'))
    suite.addTest(unittest.makeSuite(IndexingTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
