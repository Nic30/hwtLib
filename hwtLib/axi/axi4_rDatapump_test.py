#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdlObjects.specialValues import Time
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.axi.axi4_rDatapump import Axi_rDatapump
from hwtLib.interfaces.amba import Axi3_addr_withUser
from hwtLib.interfaces.amba_constants import BURST_INCR, CACHE_DEFAULT, \
    LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS, QOS_DEFAULT, RESP_OKAY


class Axi4_rDatapumpTC(SimTestCase):
    LEN_MAX = 255
    
    def setUp(self):
        u = Axi_rDatapump()
        self.u, self.model, self.procs = simPrepare(u)
    
    def mkDefaultAddrReq(self, _id, addr, _len):
        return [_id, addr, BURST_INCR, CACHE_DEFAULT, _len,
                LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS(8),
                QOS_DEFAULT]
    
    def test_nop(self):
        u = self.u
        self.doSim(200 * Time.ns)
        
        self.assertEqual(len(u.a._ag.data), 0)
        self.assertEqual(len(u.rOut._ag.data), 0)
        
    def test_notSplitedReq(self):
        u = self.u
        
        req = u.req._ag
        
        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, 0))
        self.doSim((self.LEN_MAX + 3) * Time.ns)
        
        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(u.a._ag.data), 1)
        self.assertEqual(len(u.rOut._ag.data), 0)
    
    def test_notSplitedReqWithData(self):
        u = self.u
        
        req = u.req._ag
        r = u.r._ag
        
        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, 0))
        for i in range(3):
            r.addData(i + 77)
        
        self.doSim((self.LEN_MAX + 3) * 10 * Time.ns)
        
        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(u.a._ag.data), 1)
        self.assertEqual(len(u.rOut._ag.data), 1)
        self.assertValSequenceEqual(u.rOut._ag.data[0], [0, 77, mask(64 // 8), 1])
        self.assertEqual(len(r.data), 2 - 1)  # 2. is now sended
         
    
    def test_maxNotSplitedReqWithData(self):
        u = self.u
        LEN_MAX = self.LEN_MAX
        
        req = u.req._ag
        r = u.r._ag
        rout = u.rOut._ag.data
        
        # download 256 words from addr 0xff
        req.data.append(req.mkReq(0xff, LEN_MAX))
        for i in range(LEN_MAX + 1):
            r.addData(i + 77, last=(i == LEN_MAX))

        # dummy data
        r.addData(11)
        r.addData(12)

        self.doSim(((LEN_MAX + 6) * 10) * Time.ns)
        
        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(u.a._ag.data), 1)

        # self.assertEqual(valuesToInts(u.rOut._ag.data[0]), [77, mask(64 // 8), 0, 1])
        self.assertEqual(len(r.data), 2 - 1)  # no more data was taken

        self.assertEqual(len(rout), LEN_MAX + 1)
        for i, d in enumerate(rout):
            self.assertValSequenceEqual(d, [0, 77 + i, mask(64 // 8), int(i == LEN_MAX)])
        self.assertEqual(len(r.data), 2 - 1)  # 2. is now sended
      
    def test_maxReq(self):
        u = self.u
        LEN_MAX = self.LEN_MAX
        
        req = u.req._ag
        r = u.r._ag
        ar = u.a._ag.data
        rout = u.rOut._ag.data
        
        # download 512 words from addr 0xff
        req.data.append(req.mkReq(0xff, 2 * LEN_MAX + 1))
        
        self.doSim(((LEN_MAX + 1) * 10) * Time.ns)
        
        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(ar), 2)
        self.assertEqual(len(rout), 0)
        
        for i, req in enumerate(ar):
            _id = 0
            addr = 0xff + (i * (LEN_MAX + 1) * 8)
            _len = LEN_MAX
            self.assertValSequenceEqual(req,
                                     self.mkDefaultAddrReq(_id, addr, _len))
        
    def test_maxOverlap(self):
        u = self.u
        
        req = u.req._ag
        r = u.r._ag
        ar = u.a._ag.data
        rout = u.rOut._ag.data
        
        for i in range(32):
            req.data.append(req.mkReq(i, 0))
        #    r.addData(i + 77, last=(i == 255))
        
        self.doSim(((self.LEN_MAX + 6) * 10) * Time.ns)
        
        self.assertEqual(len(req.data), 15)
        self.assertEqual(len(ar), 16)
        self.assertEqual(len(rout), 0)
        
        for i, arreq in enumerate(ar):
            _id = 0
            addr = i
            _len = 0
            self.assertValSequenceEqual(arreq,
                                     self.mkDefaultAddrReq(_id, addr, _len))
    
    def test_multipleShortest(self):
        u = self.u
        _id = 0
        
        req = u.req._ag
        r = u.r._ag
        ar = u.a._ag.data
        rout = u.rOut._ag.data
        
        for i in range(64):
            req.data.append(req.mkReq(i, 0))
            rdata = (_id, i + 1, RESP_OKAY, True)
            r.data.append(rdata)
        
        self.doSim(((64 + 4) * 10) * Time.ns)
        
        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(ar), 64)
        self.assertEqual(len(rout), 64)
        
        for i, arreq in enumerate(ar):
            addr = i
            _len = 0
            self.assertValSequenceEqual(arreq,
                                     self.mkDefaultAddrReq(_id, addr, _len))
    
    def test_multipleSplited(self):
        _id = 0
        FRAMES = 64
        l = self.LEN_MAX + 1

        u = self.u

        req = u.req._ag
        r = u.r._ag
        ar = u.a._ag.data
        rout = u.rOut._ag.data
        
        for i in range(FRAMES):
            req.data.append(req.mkReq(i, l, _id))
            for i2 in range(l + 1):
                isLast = (i2 > 0 and ((i2 % self.LEN_MAX) == 0) or (i2 == l))
                rdata = (_id, i2, RESP_OKAY, isLast)
                r.data.append(rdata)
        
        self.doSim(((len(r.data) + 4) * 10) * Time.ns)
        
        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(ar), FRAMES * 2)
        self.assertEqual(len(rout), FRAMES * (l + 1))
        
        for i, arreq in enumerate(ar):
            if i % 2 == 0:
                addr = i // 2
                _len = self.LEN_MAX
            else:
                addr = (i // 2) + 8 * (self.LEN_MAX + 1)
                _len = 0
                
            self.assertValSequenceEqual(arreq,
                                     self.mkDefaultAddrReq(_id, addr, _len))
            
        _rout = iter(rout)
        
        for i in range(FRAMES):
            for i2 in range(l + 1):
                isLast = (i2 == l)
                rdata = (_id, i2, mask(8), isLast)
                d = next(_rout)
                self.assertValSequenceEqual(d, rdata)

        
class Axi3_rDatapumpTC(Axi4_rDatapumpTC):
    LEN_MAX = 15
    def setUp(self):
        u = Axi_rDatapump(axiAddrCls=Axi3_addr_withUser)
        self.u, self.model, self.procs = simPrepare(u)
    
    def mkDefaultAddrReq(self, _id, addr, _len):
        return [_id, addr, BURST_INCR, CACHE_DEFAULT, _len,
                LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS(8),
                QOS_DEFAULT, 0]
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(Axi4_rDatapumpTC('test_maxOverlap'))
    #suite.addTest(unittest.makeSuite(Axi4_rDatapumpTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    
