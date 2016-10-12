#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hdl_toolkit.bitmask import mask
from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import valuesToInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.axi.axi4_rDatapump import Axi4_rDataPump
from hwtLib.axi.axis_measuringFifo import AxiS_measuringFifo



class AxiS_measuringFifoTC(unittest.TestCase):
    def setUp(self):
        u = AxiS_measuringFifo()
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
        
        self.assertEqual(len(u.sizes._ag.data), 0)
        self.assertEqual(len(u.dataOut._ag.data), 0)
    
    
    def test_singleWordPacket(self):
        u = self.u
        
        
        u.dataIn._ag.data.extend(((1,255,0), 
                                  (2,255,1)))

        self.doSim(200 * Time.ns)
        self.assertEqual(len(u.sizes._ag.data), 1)
        self.assertEqual(len(u.dataOut._ag.data), 2)
        

    
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_measuringFifoTC('test_nop'))
    suite.addTest(unittest.makeSuite(AxiS_measuringFifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

