#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hdl_toolkit.bitmask import mask
from hdl_toolkit.hdlObjects.specialValues import Time, NOP
from hdl_toolkit.simulator.shortcuts import simPrepare
from hdl_toolkit.simulator.simTestCase import SimTestCase
from hdl_toolkit.synthesizer.param import evalParam
from hwtLib.structManipulators.cLinkedListReader import CLinkedListReader


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
        _id = self.DEFAULT_ID
        
        u.baseAddr._ag.dout.append(0x1020)
        u.wrPtr._ag.dout.extend([NOP, N])
        
        # let spacing for request
        for i in range(N):
            u.r._ag.data.append((_id, 100 + i, mask(64 // 8), i == self.MAX_LEN))
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.req._ag.data
        self.assertEqual(len(req), 1)
        self.assertValSequenceEqual(req[0],
                                [self.DEFAULT_ID, 0x1020, self.MAX_LEN, 0])
    
        descr = u.dataOut._ag.data
        self.assertEqual(len(descr), N)
        for i, d in enumerate(descr):
            self.assertValSequenceEqual([d, ],
                                (100 + i,))
            
        
    
    def test_downloadFullBlock(self):
        u = self.u
        N = self.ITEMS_IN_BLOCK
        ADDR_BASE = 0x1020
        EXPECTED_REQ_CNT = (N + 1) // (self.MAX_LEN + 1)
        
        u.baseAddr._ag.dout.append(ADDR_BASE)
        u.wrPtr._ag.dout.extend([NOP, N])
        
        for req_i in range(EXPECTED_REQ_CNT):
            if req_i == EXPECTED_REQ_CNT - 1:
                reqId = self.LAST_ID
            else:
                reqId = self.DEFAULT_ID
        
            for i in range(self.MAX_LEN + 1):
                _r = (reqId, 1000 * req_i + i, mask(8), i == self.MAX_LEN)
                u.r._ag.data.append(_r)
        
        
        self.doSim(((self.MAX_LEN + 1) * EXPECTED_REQ_CNT + (EXPECTED_REQ_CNT + 10)) * 10 * Time.ns)
        
        req = u.req._ag.data
        reqAddrStep = (self.MAX_LEN + 1) * 8

        for i, r in enumerate(req):
            if i == EXPECTED_REQ_CNT - 1:
                reqId = self.LAST_ID
            else:
                reqId = self.DEFAULT_ID
            expected = [reqId, ADDR_BASE + i * reqAddrStep, self.MAX_LEN, 0]
            self.assertValSequenceEqual(r, expected, "(index=%d)" % i)
        self.assertEqual(len(req), EXPECTED_REQ_CNT)
        
        self.assertValSequenceEqual([u.baseAddr._ag.din[-1], ],
                                    [(1000 * (EXPECTED_REQ_CNT - 1) + self.MAX_LEN) & ~mask(3)])
    
    def test_downloadFullBlockNextAddrInSeparateReq(self):
        u = self.u
        N = self.ITEMS_IN_BLOCK
        ADDR_BASE = 0x1020
        EXPECTED_REQ_CNT = (N + 1) // (self.MAX_LEN + 1)
        
        u.baseAddr._ag.dout.append(ADDR_BASE)
        u.wrPtr._ag.dout.extend([NOP, self.MAX_LEN, NOP, NOP, NOP, N - self.MAX_LEN])
        
        for req_i in range(EXPECTED_REQ_CNT):
            if req_i == EXPECTED_REQ_CNT - 1:
                reqId = self.LAST_ID
            else:
                reqId = self.DEFAULT_ID
        
            for i in range(self.MAX_LEN + 1):
                _r = (reqId, 1000 * req_i + i, mask(8), i == self.MAX_LEN)
                u.r._ag.data.append(_r)
        
        
        self.doSim(((self.MAX_LEN + 1) * EXPECTED_REQ_CNT + (EXPECTED_REQ_CNT + 10)) * 10 * Time.ns)
        
        req = u.req._ag.data
        reqAddrStep = (self.MAX_LEN + 1) * 8

        for i, r in enumerate(req):
            if i == EXPECTED_REQ_CNT - 1:
                reqId = self.LAST_ID
            else:
                reqId = self.DEFAULT_ID
            expected = [reqId, ADDR_BASE + i * reqAddrStep, self.MAX_LEN, 0]
            self.assertValSequenceEqual(r, expected, "(index=%d)" % i)
        self.assertEqual(len(req), EXPECTED_REQ_CNT)
        
        self.assertValSequenceEqual([u.baseAddr._ag.din[-1], ],
                                    [(1000 * (EXPECTED_REQ_CNT - 1) + self.MAX_LEN) & ~mask(3)])    
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(CLinkedListReaderTC('test_singleDescrReqOnEdge2'))
    suite.addTest(unittest.makeSuite(CLinkedListReaderTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

