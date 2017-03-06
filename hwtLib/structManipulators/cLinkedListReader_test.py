#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time, NOP
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.param import evalParam
from hwtLib.structManipulators.cLinkedListReader import CLinkedListReader
from hwtLib.abstract.denseMemory import DenseMemory


class CLinkedListReaderTC(SimTestCase):
    def setUp(self):
        u = self.u = CLinkedListReader()
        self.ITEMS_IN_BLOCK = 31
        self.PTR_WIDTH = 8
        self.BUFFER_CAPACITY = 8
        self.DATA_WIDTH = 64

        def e(v):
            return evalParam(v).val

        self.ID = e(self.u.ID)
        self.ID_LAST = e(self.u.ID_LAST)
        self.MAX_LEN = self.BUFFER_CAPACITY // 2 - 1

        u.ITEMS_IN_BLOCK.set(self.ITEMS_IN_BLOCK)
        u.PTR_WIDTH.set(self.PTR_WIDTH)
        u.BUFFER_CAPACITY.set(self.BUFFER_CAPACITY)
        u.DATA_WIDTH.set(self.DATA_WIDTH)

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

        self.assertEqual(len(u.rDatapump.req._ag.data), 0)
        self.assertEqual(len(u.dataOut._ag.data), 0)

    def test_singleDescrReq(self):
        u = self.u
        t = 20

        u.baseAddr._ag.dout.append(0x1020)
        u.wrPtr._ag.dout.append(self.MAX_LEN + 1)

        self.doSim(t * 10 * Time.ns)

        req = u.rDatapump.req._ag.data
        self.assertEmpty(u.dataOut._ag.data)

        self.assertValSequenceEqual(req,
                                    [(self.ID, 0x1020, self.MAX_LEN, 0),
                                     ])

    def test_singleDescrReqOnEdge(self):
        u = self.u
        t = 20

        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(mask(self.PTR_WIDTH))
        u.wrPtr._ag.dout.append(self.MAX_LEN)  # space is self.MAX_LEN + 1

        self.doSim(t * 10 * Time.ns)

        req = u.rDatapump.req._ag.data
        self.assertEqual(len(u.dataOut._ag.data), 0)

        self.assertValSequenceEqual(req,
                                    [(self.ID, 0x1020, self.MAX_LEN, 0)])

    def test_singleDescrReqOnEdge2(self):
        u = self.u
        t = 20

        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(mask(self.PTR_WIDTH))
        u.wrPtr._ag.dout.append(self.MAX_LEN - 1)  # space is self.MAX_LEN

        self.doSim(t * 10 * Time.ns)

        req = u.rDatapump.req._ag.data
        self.assertEmpty(u.dataOut._ag.data)

        self.assertValSequenceEqual(req,
                                    [(self.ID, 0x1020, self.MAX_LEN - 1, 0),
                                     ])

    def test_singleDescrReqMax(self):
        u = self.u
        t = 20
        N = self.MAX_LEN + 1

        u.baseAddr._ag.dout.append(0x1020)
        u.wrPtr._ag.dout.append(N * (self.MAX_LEN + 1))

        self.doSim(t * 10 * Time.ns)

        req = u.rDatapump.req._ag.data
        self.assertEqual(len(u.dataOut._ag.data), 0)

        self.assertValSequenceEqual(req,
                                    [
                                     (self.ID, 0x1020, self.MAX_LEN, 0)
                                     ])

    def test_singleDescrWithData(self):
        u = self.u
        t = 25
        N = self.MAX_LEN + 1
        ADDR_BASE = 0x1020
        u.baseAddr._ag.dout.append(0x1020)
        u.wrPtr._ag.dout.extend([NOP, N])

        expectedReq, reqData = self.generateRequests(ADDR_BASE, [N])
        u.rDatapump.r._ag.data.extend(reqData)
        self.doSim(t * 10 * Time.ns)
        self.checkOutputs(expectedReq, N)

    def test_downloadFullBlock(self):
        u = self.u
        N = self.ITEMS_IN_BLOCK
        ADDR_BASE = 0x1020

        u.baseAddr._ag.dout.append(ADDR_BASE)
        u.wrPtr._ag.dout.extend([NOP, N])
        expectedReq, reqData = self.generateRequests(ADDR_BASE, [N])
        u.rDatapump.r._ag.data.extend(reqData)

        self.doSim((len(reqData) + len(expectedReq) + 50) * 10 * Time.ns)
        self.checkOutputs(expectedReq, N)

    def test_downloadFullBlockRandomized(self):
        u = self.u
        N = self.ITEMS_IN_BLOCK
        MAGIC = 6413

        m = DenseMemory(self.DATA_WIDTH, u.clk, u.rDatapump)
        
        ADDR_BASE, data = self.createBlock(m, MAGIC)
        self.updateNextAddr(m, ADDR_BASE, ADDR_BASE)
        
        self.randomize(u.rDatapump.r)
        self.randomize(u.rDatapump.req)
        self.randomize(u.dataOut)

        u.baseAddr._ag.dout.append(ADDR_BASE)
        u.wrPtr._ag.dout.extend([NOP, N])

        self.doSim(N * 60 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data, data)

    def createBlock(self, mem, seed):
        data = [i + seed for i in range(self.ITEMS_IN_BLOCK)]
        addr = mem.calloc(self.ITEMS_IN_BLOCK + 1,
                        self.DATA_WIDTH // 8,
                        keepOut=0x1020,
                        initValues=data + [None])
        return addr, data
    
    def updateNextAddr(self, mem, addrOfBlock, addrOfNextBlock):
        mem.data[addrOfBlock // mem.cellSize + self.ITEMS_IN_BLOCK] = addrOfNextBlock
    
    def test_downloadFullBlockRandomized5x(self):
        u = self.u
        N = self.ITEMS_IN_BLOCK * 5
        MAGIC = 456
        m = DenseMemory(self.DATA_WIDTH, u.clk, u.rDatapump)

        data = []
        ADDR_BASE = None
        lastAddr = None
        for i in range(5):
            a, d = self.createBlock(m, i * MAGIC)   
            if ADDR_BASE is None:
                ADDR_BASE = a
            if lastAddr is not None:
                self.updateNextAddr(m, lastAddr, a)
            lastAddr = a
            data.extend(d)
        self.updateNextAddr(m, lastAddr, ADDR_BASE)
            
        self.randomize(u.rDatapump.r)
        self.randomize(u.rDatapump.req)
        self.randomize(u.dataOut)

        u.baseAddr._ag.dout.append(ADDR_BASE)
        u.wrPtr._ag.dout.extend([NOP, N])

        self.doSim(N * 50 * Time.ns)
        
        self.assertValSequenceEqual(u.dataOut._ag.data, data)


    def test_downloadFullBlockNextAddrInSeparateReq(self):
        u = self.u
        N = self.ITEMS_IN_BLOCK + 1
        MAGIC = 5896

        m = DenseMemory(self.DATA_WIDTH, u.clk, u.rDatapump)
        
        ADDR_BASE, data = self.createBlock(m, MAGIC)
        NEXT_BASE, data2 = self.createBlock(m, MAGIC*2)
        self.updateNextAddr(m, ADDR_BASE, NEXT_BASE)

        u.baseAddr._ag.dout.append(ADDR_BASE)
        u.wrPtr._ag.dout.extend([NOP, self.MAX_LEN] 
                                + [ NOP for _ in range(self.MAX_LEN + 4)] + [N])


        self.doSim(N * 50 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data, data+ [data2[0]])
        
    def checkOutputs(self, expectedReq, itemsCnt):
        req = self.u.rDatapump.req._ag.data
        dout = self.u.dataOut._ag.data

        self.assertValSequenceEqual(req, expectedReq)

        self.assertEqual(len(dout), itemsCnt)
        for i, d in enumerate(dout):
            self.assertValEqual(d, i)

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
                elif inBlockRem == 0:
                    reqLen = 0
                    reqId = self.ID_LAST
                else:
                    if constraingSpace <= self.MAX_LEN + 1 and inBlockRem < self.MAX_LEN + 1: 
                        # we will download next* as well
                        reqLen = constraingSpace
                        reqId = self.ID_LAST
                    else:
                    # if constraingSpace == inBlockRem:
                    #    reqId = self.ID_LAST
                    #    reqLen = constraingSpace
                    # else:
                        reqLen = constraingSpace - 1

                inBlockIndex = self.ITEMS_IN_BLOCK - inBlockRem
                req = (reqId, _baseAddress + inBlockIndex * 8, reqLen, 0)
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
    # suite.addTest(CLinkedListReaderTC('test_downloadFullBlockRandomized'))
    suite.addTest(unittest.makeSuite(CLinkedListReaderTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
