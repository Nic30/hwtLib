#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hdl_toolkit.bitmask import mask
from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import valuesToInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.interfaces.amba_constants import BURST_INCR, CACHE_DEFAULT, \
    LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS, QOS_DEFAULT
from hwtLib.axi.axi4_wDatapump import Axi4_wDatapump


class Axi4_wDatapumpTC(unittest.TestCase):
    def setUp(self):
        u = Axi4_wDatapump()
        self.u, self.model, self.procs = simPrepare(u)
    
    def getTestName(self):
        className, testName = self.id().split(".")[-2:]
        return "%s_%s" % (className, testName)
    
    def doSim(self, time):
        simUnitVcd(self.model, self.procs,
                    "tmp/" + self.getTestName() + ".vcd",
                    time=time)
    
    def test_nop(self):
        u = self.u
        self.doSim(200 * Time.ns)
        
        #self.assertEqual(len(u.ar._ag.data), 0)
        #self.assertEqual(len(u.rOut._ag.data), 0)
        
 
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(Axi4_rDatapumpTC('test_maxReq'))
    suite.addTest(unittest.makeSuite(Axi4_wDatapumpTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    

