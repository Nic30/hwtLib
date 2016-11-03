#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hdl_toolkit.bitmask import mask
from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import valuesToInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.interfaces.amba_constants import BURST_INCR, CACHE_DEFAULT, \
    LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS, QOS_DEFAULT, RESP_OKAY
from hwtLib.axi.axi4_wDatapump import Axi_wDatapump
from hwtLib.axi.axi4_rDatapump_test import Axi4_rDatapumpTC
from hwtLib.interfaces.amba import Axi4_addr, Axi3_addr


class Axi4_wDatapumpTC(unittest.TestCase):
    LEN_MAX = Axi4_rDatapumpTC.LEN_MAX
    def setUp(self):
        u = Axi_wDatapump(axiAddrCls=Axi4_addr)
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
        self.assertSequenceEqual(valuesToInts(aw[0]), [0, 255, 1, 3, 0, 0, 0, 6, 0])
        
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
        self.assertSequenceEqual(valuesToInts(aw[0]), [0, 255, 1, 3, 0, 0, 0, 6, 0])
        
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
        self.assertSequenceEqual(valuesToInts(aw[0]),
                                 [0, 0xff, 1, 3, self.LEN_MAX, 0, 0, 6, 0])
        
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
            self.assertSequenceEqual(valuesToInts(rec),
                                      [0, 0xff + (8 * i), 1, 3, 0, 0, 0, 6, 0])
        
        self.assertEqual(len(w), N)
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
    # suite.addTest(Axi4_rDatapumpTC('test_maxReq'))
    suite.addTest(unittest.makeSuite(Axi3_wDatapump_direct_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    

