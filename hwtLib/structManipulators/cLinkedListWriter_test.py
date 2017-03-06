#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.param import evalParam
from hwtLib.abstract.denseMemory import DenseMemory
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
        self.DATA_WIDTH = evalParam(self.u.DATA_WIDTH).val
        
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
        
        self.assertEqual(len(u.rDatapump.req._ag.data), 0)
        self.assertEqual(len(u.wDatapump.req._ag.data), 0)
        self.assertEqual(len(u.wDatapump.w._ag.data), 0)
    
    def test_singleBurstReqNoData(self):
        u = self.u
        t = 20
        
        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.MAX_LEN + 1)
        
        self.doSim(t * 10 * Time.ns)
        
        req = u.wDatapump.req._ag.data
        self.assertEqual(len(req), 0)
        self.assertEqual(len(u.wDatapump.w._ag.data), 0)
    
    def test_singleBurst(self):
        u = self.u
        t = 20

        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.MAX_LEN + 1)

        for i in range(self.MAX_LEN + 1):
            self.u.dataIn._ag.data.append(i)

        self.doSim(t * 10 * Time.ns)

        self.assertValSequenceEqual(u.wDatapump.req._ag.data,
                                    [(self.ID, 0x1020, self.MAX_LEN, 0)])

        self.assertEqual(len(u.wDatapump.w._ag.data), self.MAX_LEN + 1)

    def test_waitForAck(self):
        u = self.u
        t = 20

        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.MAX_LEN + 1)

        for i in range(2 * (self.MAX_LEN + 1)):
            self.u.dataIn._ag.data.append(i)

        self.doSim(t * 10 * Time.ns)

        self.assertValSequenceEqual(u.wDatapump.req._ag.data,
                                    [(self.ID, 0x1020, self.MAX_LEN, 0)])

        self.assertEqual(len(u.wDatapump.w._ag.data), self.MAX_LEN + 1)

    def test_constrainedByPtrs(self):
        u = self.u
        t = 20

        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.MAX_LEN)

        for i in range(self.MAX_LEN + 1):
            self.u.dataIn._ag.data.append(i)

        self.doSim(t * 10 * Time.ns)

        self.assertValSequenceEqual(u.wDatapump.req._ag.data,
                                    [(self.ID, 0x1020, self.MAX_LEN - 1, 0)])

        self.assertEqual(len(u.wDatapump.w._ag.data), self.MAX_LEN)

    def spotNextBaseAddr(self, mem, currentBase, nextBaseAddr):
        baseIndex = currentBase // (self.DATA_WIDTH // 8)
        mem.data[baseIndex + self.ITEMS_IN_BLOCK ] = nextBaseAddr

    def test_regularUpload(self):
        u = self.u
        t = 100
        BASE = 0x1020
        ITEMS = 2 * (self.MAX_LEN + 1)
        MAGIC = 50

        u.baseAddr._ag.dout.append(BASE)
        u.rdPtr._ag.dout.append(ITEMS)

        m = DenseMemory(self.DATA_WIDTH, u.clk, u.rDatapump, u.wDatapump)

        self.spotNextBaseAddr(m, BASE, 0x2020)

        for i in range(ITEMS):
            self.u.dataIn._ag.data.append(i + MAGIC)

        self.doSim(t * 10 * Time.ns)

        baseIndex = BASE // (self.DATA_WIDTH // 8)
        # print()
        # self.debugNode(m, BASE)
        for i in range(ITEMS):
            try:
                d = m.data[baseIndex + i]
            except KeyError:
                raise AssertionError("Invalid data on index %d" % i)
            self.assertValEqual(d, i + MAGIC, "Invalid data on index %d" % i)

    def debugNode(self, mem, baseAddr):
        baseIndex = baseAddr // (self.DATA_WIDTH // 8)

        items = []
        for i in range(self.ITEMS_IN_BLOCK):
            try:
                d = mem.data[baseIndex + i]
            except KeyError:
                d = None
            items.append(d)
        try:
            nextAddr = mem.data[baseIndex + self.ITEMS_IN_BLOCK]
        except KeyError:
            nextAddr = None

        print("<Node 0x%x, items:%r\n    next:0x%x>" % (baseAddr, items, nextAddr))

    def test_regularUpload2(self):
        u = self.u
        t = 200
        BASE = 0x1020
        BASE2 = 0x2020
        ITEMS = self.ITEMS_IN_BLOCK * 2
        MAGIC = 50

        u.baseAddr._ag.dout.append(BASE)
        u.rdPtr._ag.dout.append(ITEMS)

        m = DenseMemory(self.DATA_WIDTH, u.clk, u.rDatapump, u.wDatapump)

        self.spotNextBaseAddr(m, BASE, BASE2)
        self.spotNextBaseAddr(m, BASE2, BASE + BASE2)
        self.spotNextBaseAddr(m, BASE + BASE2, BASE + BASE2 + BASE)

        for i in range(ITEMS):
            self.u.dataIn._ag.data.append(i + MAGIC)

        self.doSim(t * 10 * Time.ns)

        baseIndex = BASE // (self.DATA_WIDTH // 8)

        for i in range(ITEMS):
            try:
                d = m.data[baseIndex + i]
            except KeyError:
                raise AssertionError("Invalid data on index %d" % i)
            self.assertValEqual(d, i + MAGIC, "Invalid data on index %d" % i)
            
            
  
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(CLinkedListWriterTC('test_regularUpload'))
    suite.addTest(unittest.makeSuite(CLinkedListWriterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

