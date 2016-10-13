#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hdl_toolkit.bitmask import mask
from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.agentConnector import valuesToInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.axi.axi4_rDatapump import Axi_rDatapump
from hwtLib.interfaces.amba import Axi3_addr_withUser
from hwtLib.interfaces.amba_constants import BURST_INCR, CACHE_DEFAULT, \
    LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS, QOS_DEFAULT


class Axi4_rDatapumpTC(unittest.TestCase):
    LEN_MAX = 255
    def setUp(self):
        u = Axi_rDatapump()
        self.u, self.model, self.procs = simPrepare(u)
    
    def getTestName(self):
        className, testName = self.id().split(".")[-2:]
        return "%s_%s" % (className, testName)
    
    def doSim(self, time):
        simUnitVcd(self.model, self.procs,
                    "tmp/" + self.getTestName() + ".vcd",
                    time=time)
    
    def mkDefaultAddrReq(self, _id, addr, _len):
        return [_id, addr, BURST_INCR, CACHE_DEFAULT, _len,
                LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS(64),
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
        self.doSim(200 * Time.ns)
        
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
        
        self.doSim(200 * Time.ns)
        
        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(u.a._ag.data), 1)
        self.assertEqual(len(u.rOut._ag.data), 1)
        self.assertEqual(valuesToInts(u.rOut._ag.data[0]), [0, 77, mask(64 // 8), 1])
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

        self.doSim(2600 * Time.ns)
        
        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(u.a._ag.data), 1)

        # self.assertEqual(valuesToInts(u.rOut._ag.data[0]), [77, mask(64 // 8), 0, 1])
        self.assertEqual(len(r.data), 2 - 1)  # no more data was taken

        self.assertEqual(len(rout), LEN_MAX + 1)
        for i, d in enumerate(rout):
            d = valuesToInts(d)
            self.assertEqual(d, [0, 77 + i, mask(64 // 8), int(i == LEN_MAX)])
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
        
        self.doSim(2600 * Time.ns)
        
        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(ar), 2)
        self.assertEqual(len(rout), 0)
        
        for i, req in enumerate(ar):
            _id = 0
            addr = 0xff + (i * (LEN_MAX + 1) * 8)
            _len = LEN_MAX
            self.assertSequenceEqual(valuesToInts(req),
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
        
        self.doSim(1000 * Time.ns)
        
        self.assertEqual(len(req.data), 15)
        self.assertEqual(len(ar), 16)
        self.assertEqual(len(rout), 0)
        
        for i, arreq in enumerate(ar):
            _id = 0
            addr = i
            _len = 0
            self.assertSequenceEqual(valuesToInts(arreq),
                                     self.mkDefaultAddrReq(_id, addr, _len))
        
        
class Axi3_rDatapumpTC(Axi4_rDatapumpTC):
    LEN_MAX = 15
    def setUp(self):
        u = Axi_rDatapump(axiAddrCls=Axi3_addr_withUser)
        self.u, self.model, self.procs = simPrepare(u)
    
    def mkDefaultAddrReq(self, _id, addr, _len):
        return [_id, addr, BURST_INCR, CACHE_DEFAULT, _len,
                LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS(64),
                QOS_DEFAULT, 0]
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(Axi4_rDatapumpTC('test_maxReq'))
    suite.addTest(unittest.makeSuite(Axi3_rDatapumpTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    
