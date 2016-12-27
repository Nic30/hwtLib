#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import selectBit
from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import autoAddAgents, agInts
from hwt.simulator.shortcuts import simUnitVcd
from hwt.synthesizer.shortcuts import synthesised
from hwtLib.samples.iLvl.operators.concat import SimpleConcat


def addValues(unit, data):
    for d in data:
        # because there are 4 bits
        for i in range(4):
            databit = getattr(unit, "a%d" % i)
            if d is None:
                dataBitval = None
            else:
                dataBitval = selectBit(d, i)
            
            databit._ag.data.append(dataBitval)

class ConcatTC(unittest.TestCase):
    def setUpUnit(self, unit):
        self.u = unit
        synthesised(self.u)
        self.procs = autoAddAgents(self.u)
    
    def runSim(self, name, time=80 * Time.ns):
        simUnitVcd(self.u, self.procs,
                "tmp/concat_%s.vcd" % name,
                time=time)
            
    def test_join(self):
        self.setUpUnit(SimpleConcat())
        u = self.u
        
        #addValues(u, [0, 1, 2, 4, 8, (1 << 4) - 1, None, 3, 2, 1])
        addValues(u, [2, 4, (1 << 4) - 1, None, 3, 2, 1])
        
        self.runSim("join")
        
        self.assertSequenceEqual([2, 4, 15, None, 3, 2, 1, 1], agInts(u.a_out))
        
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(IndexingTC('test_rangeJoin'))
    suite.addTest(unittest.makeSuite(ConcatTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
