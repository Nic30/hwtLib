#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hdl_toolkit.bitmask import mask
from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import valuesToInts, valToInt
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
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
        
        u.dataIn._ag.data.extend([(2, 255, 1),
                                  ])

        self.doSim(200 * Time.ns)
        self.assertEqual(len(u.sizes._ag.data), 1)
        self.assertEqual(len(u.dataOut._ag.data), 1)

    def test_singleWordPacketWithDelay(self):
        u = self.u
        
        u.dataIn._ag.data.extend([(2, 255, 1),
                                  ])
        u.dataOut._ag.enable = False

        self.doSim(200 * Time.ns)
        self.assertEqual(len(u.sizes._ag.data), 1)
        self.assertEqual(len(u.dataOut._ag.data), 0)
        self.assertEqual(valToInt(self.model.dataOut_last._val), 1)



    def test_multiplePackets(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data
        
        u.dataIn._ag.data.extend([(1, 255, 1),
                                  (2, 255, 1),
                                  (3, 255, 1)
                                  ])

        self.doSim(200 * Time.ns)
        self.assertEqual(len(sizes), 3)
        self.assertEqual(len(data), 3)
        self.assertSequenceEqual(valuesToInts(sizes), (8, 8, 8))

        
    def test_doubleWordPacket(self):
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data
        
        u.dataIn._ag.data.extend([(1, 255, 0),
                                  (2, 255, 1)
                                 ])

        self.doSim(200 * Time.ns)
        self.assertEqual(len(sizes), 1)
        self.assertEqual(len(data), 2)
        self.assertSequenceEqual(valuesToInts(sizes), (16,))
    
    def test_unalignedPacket(self):    
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data
        
        u.dataIn._ag.data.extend([(1, 255, 0),
                                  (2, 1, 1)
                                 ])
        self.doSim(200 * Time.ns)
        self.assertEqual(len(sizes), 1)
        self.assertEqual(len(data), 2)
        self.assertSequenceEqual(valuesToInts(sizes), (9,))
    
    def test_unalignedPacket1Word(self):    
        u = self.u
        sizes = u.sizes._ag.data
        data = u.dataOut._ag.data
        
        u.dataIn._ag.data.extend([
                                  (2, 1, 1),
                                 ])
        self.doSim(200 * Time.ns)
        self.assertEqual(len(sizes), 1)
        self.assertEqual(len(data), 1)
        self.assertSequenceEqual(valuesToInts(sizes), (1,))
    
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_measuringFifoTC('test_nop'))
    suite.addTest(unittest.makeSuite(AxiS_measuringFifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

