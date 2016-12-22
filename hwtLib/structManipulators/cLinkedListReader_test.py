#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdlObjects.specialValues import Time, NOP
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.param import evalParam
from hwtLib.structManipulators.cLinkedListReader import CLinkedListReader
from hwt.simulator.utils import agent_randomize


class CLinkedListReaderTC(SimTestCase):
    def setUp(self):
        self.u = CLinkedListReader()
        self.ITEMS_IN_BLOCK = 31
        self.RING_SPACE_WIDTH = 8
        self.BUFFER_CAPACITY = 8
        self.DEFAULT_ID = evalParam(self.u.DEFAULT_ID).val
        self.LAST_ID = evalParam(self.u.LAST_ID).val
        self.MAX_LEN = self.BUFFER_CAPACITY // 2 - 1
        
        self.u.ITEMS_IN_BLOCK.set(self.ITEMS_IN_BLOCK)
        self.u.RING_SPACE_WIDTH.set(self.RING_SPACE_WIDTH)
        self.u.BUFFER_CAPACITY.set(self.BUFFER_CAPACITY)
        
        _, self.model, self.procs = simPrepare(self.u)
    
    def test_tailHeadPrincipe(self):
        BITS = 16
        MASK = mask(BITS)
        tail = 0
        head = 0

        def normalize(n):
            if n < 0:
                return MASK + n
            elif n > MASK:
                return n - MASK
            else:
                return n
        
        def size():
            return normalize(head - tail)
    
        
        self.assertEqual(size(), 0)
        
        head = MASK
        
        self.assertEqual(size(), MASK)
        
        tail = 10 
        self.assertEqual(size(), MASK - 10)
        
        head = normalize(head + 5)
        self.assertEqual(size(), MASK - 5)
    
    def test_nop(self):
        u = self.u
        self.doSim(200 * Time.ns)
        
        self.assertEqual(len(u.req._ag.data), 0)
        self.assertEqual(len(u.dataOut._ag.data), 0)
    
    def test_singleDescrReq(self):
        u = self.u
        t = 20
        
        u.baseAddr._ag.dout.append(0x1020)
        u.wrPtr._ag.dout.append(self.MAX_LEN + 1)
        
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.req._ag.data
        self.assertEqual(len(req), 1)
        self.assertEqual(len(u.dataOut._ag.data), 0)
    
        self.assertValSequenceEqual(req[0],
                                [self.DEFAULT_ID, 0x1020, self.MAX_LEN, 0])
    
    def test_singleDescrReqOnEdge(self):
        u = self.u
        t = 20
        
        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(mask(self.RING_SPACE_WIDTH))
        u.wrPtr._ag.dout.append(self.MAX_LEN)  # space is self.MAX_LEN + 1 
        
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.req._ag.data
        self.assertEqual(len(req), 1)
        self.assertEqual(len(u.dataOut._ag.data), 0)
    
        self.assertValSequenceEqual(req[0],
                                [self.DEFAULT_ID, 0x1020, self.MAX_LEN, 0])
    
    def test_singleDescrReqOnEdge2(self):
        u = self.u
        t = 20
        
        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(mask(self.RING_SPACE_WIDTH))
        u.wrPtr._ag.dout.append(self.MAX_LEN - 1)  # space is self.MAX_LEN
        
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.req._ag.data
        self.assertEqual(len(req), 1)
        self.assertEqual(len(u.dataOut._ag.data), 0)
    
        self.assertValSequenceEqual(req[0],
                                [self.DEFAULT_ID, 0x1020, self.MAX_LEN - 1, 0])
    
    def test_singleDescrReqMax(self):
        u = self.u
        t = 20
        N = self.MAX_LEN + 1
        
        u.baseAddr._ag.dout.append(0x1020)
        u.wrPtr._ag.dout.append(N * (self.MAX_LEN + 1))
        
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.req._ag.data
        self.assertEqual(len(req), 1)
        self.assertEqual(len(u.dataOut._ag.data), 0)
    
        self.assertValSequenceEqual(req[0],
                                [self.DEFAULT_ID, 0x1020, self.MAX_LEN, 0])
    
    def test_singleDescrWithData(self):
        u = self.u
        t = 25
        N = self.MAX_LEN + 1
        ADDR_BASE = 0x1020
        u.baseAddr._ag.dout.append(0x1020)
        u.wrPtr._ag.dout.extend([NOP, N])
        
        expectedReq, reqData = self.generateRequests(ADDR_BASE, [N])
        u.r._ag.data.extend(reqData)
        self.doSim(t * 10 * Time.ns)
        self.checkOutputs(expectedReq, N)
        
    def test_downloadFullBlock(self):
        u = self.u
        N = self.ITEMS_IN_BLOCK
        ADDR_BASE = 0x1020
        
        u.baseAddr._ag.dout.append(ADDR_BASE)
        u.wrPtr._ag.dout.extend([NOP, N])
        expectedReq, reqData = self.generateRequests(ADDR_BASE, [N])
        u.r._ag.data.extend(reqData)
        
        self.doSim((len(reqData) + len(expectedReq) + 50) * 10 * Time.ns)
        self.checkOutputs(expectedReq, N)

    #def test_downloadFullBlockRandomized(self):
    #    randomize = lambda intf: self.procs.append(agent_randomize(intf._ag))
    #    u = self.u
    #    N = self.ITEMS_IN_BLOCK
    #    ADDR_BASE = 0x1020
    #    randomize(u.r)
    #    randomize(u.req)
    #    randomize(u.dataOut)
    #    
    #    
    #    u.baseAddr._ag.dout.append(ADDR_BASE)
    #    u.wrPtr._ag.dout.extend([NOP, N])
    #    expectedReq, reqData = self.generateRequests(ADDR_BASE, [N])
    #    u.r._ag.data.extend(reqData)
    #    
    #    self.doSim((len(reqData) + len(expectedReq) + 50) * 2 * 10 * Time.ns)
    #    self.checkOutputs(expectedReq, N)
    #    
    #
    #def test_downloadFullBlockRandomized5x(self):
    #    randomize = lambda intf: self.procs.append(agent_randomize(intf._ag))
    #    u = self.u
    #    N = self.ITEMS_IN_BLOCK*5
    #    ADDR_BASE = 0x1020
    #    randomize(u.r)
    #    randomize(u.req)
    #    randomize(u.dataOut)
    #    
    #    
    #    u.baseAddr._ag.dout.append(ADDR_BASE)
    #    u.wrPtr._ag.dout.extend([NOP, N])
    #    expectedReq, reqData = self.generateRequests(ADDR_BASE, [N])
    #    u.r._ag.data.extend(reqData)
    #    
    #    self.doSim((len(reqData) + len(expectedReq) + 50) * 2 * 10 * Time.ns)
    #    self.checkOutputs(expectedReq, N)                  
              
    def test_downloadFullBlockNextAddrInSeparateReq(self):
        u = self.u
        N = self.ITEMS_IN_BLOCK + 1
        ADDR_BASE = 0x1020
        
        u.baseAddr._ag.dout.append(ADDR_BASE)
        u.wrPtr._ag.dout.extend([NOP, self.MAX_LEN] + [ NOP for _ in range(self.MAX_LEN + 4)] + [ N ])
        
        expectedReq, reqData = self.generateRequests(ADDR_BASE, [self.MAX_LEN, N - self.MAX_LEN - 1])
        self.u.r._ag.data.extend(reqData)
        
        self.doSim((len(reqData) + len(expectedReq) + 50) * 10 * Time.ns)
        self.checkOutputs(expectedReq, N - 1)
    
    def checkOutputs(self, expectedReq, itemsCnt):
        req = self.u.req._ag.data
        dout = self.u.dataOut._ag.data

        for i, expected in enumerate(expectedReq):
            _req = req[i] 
            self.assertValSequenceEqual(_req, expected, "(index=%d)" % i)
    
        self.assertEqual(len(dout), itemsCnt)
        for i, d in enumerate(dout):
            self.assertValSequenceEqual([d, ], (i,))
    
    def generateRequests(self, baseAddress, spaceValues):
        """
        generate reference requests and data
        data words are containing it's indexes, baseAddresses are multiplies baseAddress
        @param spaceValues: is iterable of space values
        """
        requests = []
        responses = []
        wordCntr = 0
        inBlockRem = self.ITEMS_IN_BLOCK
        _baseAddress = baseAddress
        
        for space in spaceValues:
            while space != 0:
                constraingSpace = min(inBlockRem, space)
                reqId = self.DEFAULT_ID
                if constraingSpace > self.MAX_LEN + 1:
                    reqLen = self.MAX_LEN
                elif constraingSpace == 0:
                    reqLen = 0
                else:
                    if constraingSpace <= self.MAX_LEN + 1 and inBlockRem < self.MAX_LEN + 1: 
                        # we will download next* as well
                        reqLen = constraingSpace
                        reqId = self.LAST_ID
                    else:
                        reqLen = constraingSpace - 1
                    
                    
                inBlockIndex = self.ITEMS_IN_BLOCK - inBlockRem
                req = [reqId, _baseAddress + inBlockIndex * 8 , reqLen, 0]
                requests.append(req)

                for i in range(reqLen + 1):
                    if i == reqLen and reqId == self.LAST_ID:
                        r = (reqId, baseAddress, mask(8), True)
                        _baseAddress += baseAddress
                    else:
                        r = (reqId, wordCntr + i, mask(8), i == reqLen)
                
                    responses.append(r)
                
                if reqId == self.LAST_ID:
                    inBlockRem = self.ITEMS_IN_BLOCK
                    wordCntr += reqLen
                    space -= reqLen
                else:
                    inBlockRem -= reqLen + 1
                    wordCntr += reqLen + 1
                    space -= reqLen + 1
        
        return requests, responses        
          
if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(CLinkedListReaderTC('test_downloadFullBlockRandomized'))
    suite.addTest(unittest.makeSuite(CLinkedListReaderTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

