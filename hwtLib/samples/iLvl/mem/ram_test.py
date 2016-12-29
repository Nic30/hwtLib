#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts, valuesToInts
from hwt.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.samples.iLvl.mem.ram import SimpleAsyncRam, SimpleSyncRam


class RamTC(unittest.TestCase):
    def setUpAsync(self):
        self.u, self.model, self.procs = simPrepare(SimpleAsyncRam())
    
    def setUpSync(self):
        self.u, self.model, self.procs = simPrepare(SimpleSyncRam())
         
    def runSim(self, name, time=80 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/ram_%s.vcd" % name,
                time=time)
            
    def test_async_allData(self):
        self.setUpAsync()
        u = self.u
        
        u.addr_in._ag.data = [0, 1, 2, 3, None, 3, 2, 1]
        u.addr_out._ag.data = [None, 0, 1, 2, 3, None, 0, 1]
        u.din._ag.data = [10, 11, 12, 13, 14, 15, 16, 17]
        self.runSim("async_allData")
        
        
        self.assertSequenceEqual(valuesToInts(self.model.ram_data._val.val), [None, 17, 16, 15])
        self.assertSequenceEqual(agInts(u.dout), [None, 10, 11, 12, None, None, None, 17])

    def test_sync_allData(self):
        self.setUpSync()
        u = self.u
        
        u.addr_in._ag.data = [0, 1, 2, 3, None, 3, 2, 1]
        u.addr_out._ag.data = [None, 0, 1, 2, 3, None, 0, 1]
        u.din._ag.data = [10, 11, 12, 13, 14, 15, 16, 17]
        self.runSim("sync_allData")
        
        
        self.assertSequenceEqual(valuesToInts(self.model.ram_data._val.val), [None, 17, 16, 15])
        self.assertSequenceEqual(agInts(u.dout), [None, None, 10, 11, 12, 13, None, None]) 
               
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(RamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
   

 
