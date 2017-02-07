#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.param import evalParam
from hwtLib.structManipulators.cLinkedListWriter import CLinkedListWriter


class CLinkedListWriterTC(SimTestCase):
    def setUp(self):
        self.u = CLinkedListWriter()
        self.ITEMS_IN_BLOCK = 31
        self.PTR_WIDTH = 8
        self.BUFFER_CAPACITY = 7
        self.TIMEOUT = 40 
        self.ID = evalParam(self.u.ID).val
        self.MAX_LEN = self.BUFFER_CAPACITY // 2 - 1
        
        self.u.TIMEOUT.set(self.TIMEOUT)
        self.u.ITEMS_IN_BLOCK.set(self.ITEMS_IN_BLOCK)
        self.u.PTR_WIDTH.set(self.PTR_WIDTH)
        self.u.BUFFER_CAPACITY.set(self.BUFFER_CAPACITY)
        
        
        _, self.model, self.procs = simPrepare(self.u)
    
    def test_nop(self):
        u = self.u
        for i in range(self.MAX_LEN + 1):
            self.u.dataIn._ag.data.append(i)
            
        self.doSim((self.TIMEOUT + 10) * 10 * Time.ns)
        
        self.assertEqual(len(u.rReq._ag.data), 0)
        self.assertEqual(len(u.wReq._ag.data), 0)
        self.assertEqual(len(u.w._ag.data), 0)
    
    def test_singleBurstReqNoData(self):
        u = self.u
        t = 20
        
        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.MAX_LEN + 1)
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.wReq._ag.data
        self.assertEqual(len(req), 0)
        self.assertEqual(len(u.w._ag.data), 0)
    
    def test_singleBurst(self):
        u = self.u
        t = 20
        
        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.MAX_LEN + 1)
        
        for i in range(self.MAX_LEN + 1):
            self.u.dataIn._ag.data.append(i)
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.wReq._ag.data
        self.assertEqual(len(req), 1)
        self.assertValSequenceEqual(req[0],
                                [self.ID, 0x1020, self.MAX_LEN, 0])

        self.assertEqual(len(u.w._ag.data), self.MAX_LEN + 1)

    def test_waitForAck(self):
        u = self.u
        t = 20
        
        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.MAX_LEN + 1)
        
        for i in range(2 * (self.MAX_LEN + 1)):
            self.u.dataIn._ag.data.append(i)
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.wReq._ag.data
        self.assertEqual(len(req), 1)
        self.assertValSequenceEqual(req[0],
                                [self.ID, 0x1020, self.MAX_LEN, 0])

        self.assertEqual(len(u.w._ag.data), self.MAX_LEN + 1)
    
    
    def test_constrainedByPtrs(self):
        u = self.u
        t = 20
        
        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.MAX_LEN)
        
        for i in range(self.MAX_LEN + 1):
            self.u.dataIn._ag.data.append(i)
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.wReq._ag.data
        self.assertEqual(len(req), 1)
        self.assertValSequenceEqual(req[0],
                                [self.ID, 0x1020, self.MAX_LEN - 1, 0])

        self.assertEqual(len(u.w._ag.data), self.MAX_LEN)
    
    
    
          
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(CLinkedListWriterTC('test_constrainedByPtrs'))
    suite.addTest(unittest.makeSuite(CLinkedListWriterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

