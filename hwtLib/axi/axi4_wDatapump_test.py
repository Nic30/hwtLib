#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdlObjects.specialValues import Time
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.axi.axi4_rDatapump_test import Axi4_rDatapumpTC
from hwtLib.axi.axi4_wDatapump import Axi_wDatapump
from hwtLib.interfaces.amba import Axi4_addr, Axi3_addr
from hwtLib.interfaces.amba_constants import   RESP_OKAY, BYTES_IN_TRANS


class Axi4_wDatapumpTC(SimTestCase):
    LEN_MAX = Axi4_rDatapumpTC.LEN_MAX

    def setUp(self):
        u = Axi_wDatapump(axiAddrCls=Axi4_addr)
        self.u, self.model, self.procs = simPrepare(u)
    
    def test_nop(self):
        u = self.u
        
        self.doSim(200 * Time.ns)
        
        self.assertEqual(len(u.a._ag.data), 0)
        self.assertEqual(len(u.w._ag.data), 0)
        
    def test_simple(self):
        u = self.u
        
        req = u.req._ag
        aw = u.a._ag.data
        
        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, 0))
        
        self.doSim(200 * Time.ns)
        
        self.assertEqual(len(aw), 1)
        self.assertValSequenceEqual(aw[0], [0, 255, 1, 3, 0, 0, 0, BYTES_IN_TRANS(8), 0])
        
        self.assertEqual(len(u.w._ag.data), 0)
    
    def test_simpleWithData(self):
        u = self.u
        
        req = u.req._ag
        aw = u.a._ag.data
        wIn = u.wIn._ag
        w = u.w._ag.data
        b = u.b._ag.data
        
        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, 0))
        wIn.data.append((77, mask(64 // 8 - 1), 1))
        b.append((0, RESP_OKAY))
        
        self.doSim(200 * Time.ns)
        
        self.assertEqual(len(aw), 1)
        self.assertValSequenceEqual(aw[0], [0, 255, 1, 3, 0, 0, 0, BYTES_IN_TRANS(8), 0])
        
        self.assertEqual(len(w), 1)
        self.assertEqual(len(b), 0)
        
    def test_singleLong(self):
        u = self.u
        
        req = u.req._ag
        aw = u.a._ag.data
        wIn = u.wIn._ag
        w = u.w._ag.data
        b = u.b._ag.data
        
        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, self.LEN_MAX))
        for i in range(self.LEN_MAX + 1 + 10):
            wIn.data.append((100 + 1, mask(8), i == self.LEN_MAX))
        b.append((0, RESP_OKAY))
        
        self.doSim((10 + self.LEN_MAX) * 10 * Time.ns)
        
        self.assertEqual(len(aw), 1)
        self.assertValSequenceEqual(aw[0],
                                 [0, 0xff, 1, 3, self.LEN_MAX, 0, 0, BYTES_IN_TRANS(8), 0])
        
        self.assertEqual(len(w), self.LEN_MAX + 1)
        self.assertEqual(len(b), 0)
        self.assertEqual(len(u.reqAck._ag.data), 1)
        
    
    def test_multiple(self):
        u = self.u
        req = u.req._ag
        aw = u.a._ag.data
        wIn = u.wIn._ag
        w = u.w._ag.data
        b = u.b._ag.data
        N = 50
        
        # download one word from addr 0xff
        for i in range(N):
            req.data.append(req.mkReq((i * 8) + 0xff, 0))
            wIn.data.append((77, mask(64 // 8 - 1), 1))
            b.append((0, RESP_OKAY))
        
        self.doSim(1000 * Time.ns)
        
        self.assertEqual(len(aw), N)
        for i, rec in enumerate(aw):
            self.assertValSequenceEqual(rec,
                                      [0, 0xff + (8 * i), 1, 3, 0, 0, 0, BYTES_IN_TRANS(8), 0])
        
        self.assertEqual(len(w), N)
        self.assertEqual(len(b), 0)
        self.assertEqual(len(u.reqAck._ag.data), N)
        
    def test_multiple_randomized(self):
        u = self.u
        req = u.req._ag
        aw = u.a._ag.data
        wIn = u.wIn._ag
        w = u.w._ag.data
        b = u.b._ag.data
        N = 50
        
        # download one word from addr 0xff
        for i in range(N):
            req.data.append(req.mkReq((i * 8) + 0xff, 0))
            wIn.data.append((77, mask(64 // 8 - 1), 1))
            b.append((0, RESP_OKAY))
        
        ra = self.randomize
        ra(u.a)
        ra(u.b)
        ra(u.req)
        ra(u.reqAck)
        ra(u.w)
        ra(u.wIn)
        
        self.doSim(1200 * Time.ns)
        
        self.assertEqual(len(aw), N)
        for i, rec in enumerate(aw):
            self.assertValSequenceEqual(rec,
                                      [0, 0xff + (8 * i), 1, 3, 0, 0, 0, BYTES_IN_TRANS(8), 0])
        
        self.assertEqual(len(w), N)
        self.assertEqual(len(b), 0)
        self.assertEqual(len(u.reqAck._ag.data), N)
        
    def test_multiple_randomized2(self):
        u = self.u
        req = u.req._ag
        aw = u.a._ag.data
        wIn = u.wIn._ag
        w = u.w._ag.data
        b = u.b._ag.data
        N = 50
        L = 3
        expectedWData = []
        
        
        # download one word from addr 0xff
        for i in range(N):
            req.data.append(req.mkReq((i * 8) + 0xff, L - 1))
            for i in range(L):
                d = 77 + i
                m = mask(64 // 8 - 1)
                l = i == (L - 1)
                wIn.data.append((d, m, l))
                expectedWData.append((0, d, m, int(l)))
            b.append((0, RESP_OKAY))
        
        ra = self.randomize
        ra(u.a)
        ra(u.b)
        ra(u.req)
        ra(u.reqAck)
        ra(u.w)
        ra(u.wIn)
        
        self.doSim(N * L * 25 * Time.ns)
        
        self.assertEqual(len(aw), N)
        for i, rec in enumerate(aw):
            self.assertValSequenceEqual(rec,
                                      [0, 0xff + (8 * i), 1, 3, L - 1, 0, 0, BYTES_IN_TRANS(8), 0])
        
        self.assertEqual(len(w), N * 3)
        for expWD, wd in zip(expectedWData, w):
            self.assertValSequenceEqual(wd, expWD)
            
        self.assertEqual(len(b), 0)
        self.assertEqual(len(u.reqAck._ag.data), N)
     
class Axi3_wDatapump_direct_TC(Axi4_wDatapumpTC):
    LEN_MAX = 16
    def setUp(self):
        u = Axi_wDatapump(axiAddrCls=Axi3_addr)
        u.MAX_LEN.set(16)
        self.u, self.model, self.procs = simPrepare(u)
            


       
if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(Axi4_wDatapumpTC('test_multiple_randomized2'))
    suite.addTest(unittest.makeSuite(Axi3_wDatapump_direct_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    

