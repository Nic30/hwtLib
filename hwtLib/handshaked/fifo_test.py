#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import copy
import unittest

from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import Handshaked
from hwt.simulator.shortcuts import simPrepare
from hwtLib.handshaked.fifo import HandshakedFifo
from hwt.simulator.simTestCase import SimTestCase


class HsFifoTC(SimTestCase):
    def setUp(self):
        self.u = HandshakedFifo(Handshaked)
        self.u.DEPTH.set(8)
        self.u.DATA_WIDTH.set(4)
        self.u.EXPORT_SIZE.set(True)
        _, self.model, self.procs = simPrepare(self.u)
    
    def test_stuckedData(self):
        u = self.u
        u.dataIn._ag.data = [1]

        u.dataOut._ag.enable = False
        self.doSim(120 * Time.ns)
        self.assertValEqual(self.model.dataOut_data, 1)
        
    def test_withPause(self):
        u = self.u
        golden = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        u.dataIn._ag.data = copy(golden)

        def pause(simulator):
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataOut._ag.enable = False
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataOut._ag.enable = True  
            yield simulator.wait(3 * 10 * Time.ns)  
            u.dataIn._ag.enable = False
            yield simulator.wait(3 * 10 * Time.ns)  
            u.dataIn._ag.enable = True
        
        self.procs.append(pause)

        self.doSim(200 * Time.ns)
        
        self.assertValSequenceEqual(u.dataOut._ag.data, golden)
        self.assertSequenceEqual(u.dataIn._ag.data, [])
    
    def test_withPause2(self):
        u = self.u
        golden = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        u.dataIn._ag.data = copy(golden)

        def pause(simulator):
            yield simulator.wait(4 * 10 * Time.ns)
            u.dataOut._ag.enable = False
            yield simulator.wait(3 * 10 * Time.ns)
            u.dataOut._ag.enable = True  
            yield simulator.wait(3 * 10 * Time.ns)  
            u.dataIn._ag.enable = False
            yield simulator.wait(3 * 10 * Time.ns)  
            u.dataIn._ag.enable = True
        
        self.procs.append(pause)

        self.doSim(200 * Time.ns)
        
        self.assertValSequenceEqual(u.dataOut._ag.data, golden)
        self.assertSequenceEqual(u.dataIn._ag.data, [])   
         
    def test_passdata(self):
        u = self.u
        golden = [1, 2, 3, 4, 5, 6]
        u.dataIn._ag.data = copy(golden)

        self.doSim(120 * Time.ns)
        
        self.assertValSequenceEqual(u.dataOut._ag.data, golden)
        self.assertValSequenceEqual(u.dataIn._ag.data, [])

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(HsFifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
