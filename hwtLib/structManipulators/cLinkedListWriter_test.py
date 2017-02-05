#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time, NOP
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.param import evalParam
from hwtLib.structManipulators.cLinkedListWriter import CLinkedListWriter


class CLinkedListWriterTC(SimTestCase):
    def setUp(self):
        self.u = CLinkedListWriter()
        self.ITEMS_IN_BLOCK = 31
        self.PTR_WIDTH = 8
        self.BUFFER_CAPACITY = 8
        self.TIMEOUT = 40 
        self.ID = evalParam(self.u.ID).val
        self.MAX_LEN = self.BUFFER_CAPACITY // 2 - 1
        
        self.u.TIMEOUT.set(self.TIMEOUT)
        self.u.ITEMS_IN_BLOCK.set(self.ITEMS_IN_BLOCK)
        self.u.PTR_WIDTH.set(self.PTR_WIDTH)
        self.u.BUFFER_CAPACITY.set(self.BUFFER_CAPACITY)
        
        self.RD_START = (1 << self.PTR_WIDTH) - 1
        
        _, self.model, self.procs = simPrepare(self.u)
    
    def test_nop(self):
        u = self.u
        self.doSim((self.TIMEOUT + 10) * 10 * Time.ns)
        
        self.assertEqual(len(u.rReq._ag.data), 0)
        self.assertEqual(len(u.wReq._ag.data), 0)
        self.assertEqual(len(u.w._ag.data), 0)
    
    def test_singleDescrReqNoData(self):
        u = self.u
        t = 20
        
        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.RD_START - (self.MAX_LEN + 1))
        
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.wReq._ag.data
        self.assertEqual(len(req), 0)
        self.assertEqual(len(u.w._ag.data), 0)
    
    def test_singleDescr(self):
        u = self.u
        t = 20
        
        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.RD_START - (self.MAX_LEN + 1))
        
        for i in range(self.MAX_LEN+1):
            self.u.dataIn._ag.data.append(i)
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.wReq._ag.data
        self.assertEqual(len(req), 1)
        self.assertEqual(len(u.w._ag.data), self.MAX_LEN+1)
    
        self.assertValSequenceEqual(req[0],
                                [self.ID, 0x1020, self.MAX_LEN, 0])
    
    def test_singleDescrReqOnEdge(self):
        u = self.u
        t = 20
        
        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(mask(self.PTR_WIDTH))
        u.wrPtr._ag.dout.append(self.MAX_LEN)  # space is self.MAX_LEN + 1 
        
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.req._ag.data
        self.assertEqual(len(req), 1)
        self.assertEqual(len(u.dataOut._ag.data), 0)
    
        self.assertValSequenceEqual(req[0],
                                [self.ID, 0x1020, self.MAX_LEN, 0])
    
    def test_singleDescrReqOnEdge2(self):
        u = self.u
        t = 20
        
        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(mask(self.PTR_WIDTH))
        u.wrPtr._ag.dout.append(self.MAX_LEN - 1)  # space is self.MAX_LEN
        
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.req._ag.data
        self.assertEqual(len(req), 1)
        self.assertEqual(len(u.dataOut._ag.data), 0)
    
        self.assertValSequenceEqual(req[0],
                                [self.ID, 0x1020, self.MAX_LEN - 1, 0])
    
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
                                [self.ID, 0x1020, self.MAX_LEN, 0])
    
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
                reqId = self.ID
                if constraingSpace > self.MAX_LEN + 1:
                    reqLen = self.MAX_LEN
                elif constraingSpace == 0:
                    reqLen = 0
                else:
                    if constraingSpace <= self.MAX_LEN + 1 and inBlockRem < self.MAX_LEN + 1: 
                        # we will download next* as well
                        reqLen = constraingSpace
                        reqId = self.ID_LAST
                    else:
                        reqLen = constraingSpace - 1
                    
                    
                inBlockIndex = self.ITEMS_IN_BLOCK - inBlockRem
                req = [reqId, _baseAddress + inBlockIndex * 8 , reqLen, 0]
                requests.append(req)

                for i in range(reqLen + 1):
                    if i == reqLen and reqId == self.ID_LAST:
                        r = (reqId, baseAddress, mask(8), True)
                        _baseAddress += baseAddress
                    else:
                        r = (reqId, wordCntr + i, mask(8), i == reqLen)
                
                    responses.append(r)
                
                if reqId == self.ID_LAST:
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
    suite.addTest(CLinkedListWriterTC('test_singleDescr'))
    # suite.addTest(unittest.makeSuite(CLinkedListWriterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

