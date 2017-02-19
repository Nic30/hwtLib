#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil
import unittest

from hwt.hdlObjects.constants import Time, NOP
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import agent_randomize
from hwt.synthesizer.param import evalParam
from hwtLib.structManipulators.arrayBuff_writer import ArrayBuff_writer


class ArrayBuff_writer_TC(SimTestCase):
    def setUp(self):
        self.u = ArrayBuff_writer()
        self.u.TIMEOUT.set(32)
        _, self.model, self.procs = simPrepare(self.u)
 
    def test_nop(self):
        u = self.u
        self.doSim(40 * 10 * Time.ns)
        self.assertEqual(len(u.wDatapump.req._ag.data), 0)
        self.assertEqual(len(u.wDatapump.w._ag.data), 0)
        
        self.assertValEqual(self.u.uploaded._ag.data[-1], 0)
        
    def test_timeout(self):
        u = self.u
        u.items._ag.data.append(16)
        u.baseAddr._ag.dout.append(0x1230)
        
        self.doSim(40 * 10 * Time.ns)
        
        req = u.wDatapump.req._ag.data
        self.assertEqual(len(u.items._ag.data), 0)
        self.assertEqual(len(req), 1)
        self.assertValSequenceEqual(req[0], [3, 0x1230, 0, 0])
        
        w = u.wDatapump.w._ag.data
        self.assertEqual(len(w), 1)
        self.assertValSequenceEqual(w[0], [16, 255, 1])
        self.assertValEqual(self.u.uploaded._ag.data[-1], 0)
    
    def test_multipleTimeout(self):
        u = self.u
        
        u.baseAddr._ag.dout.append(0x1230)
        _id = evalParam(u.ID).val
        
        def itemsWithDelay(sim):
            addSize = u.items._ag.data.append
            addSize(16)
            yield sim.wait(40 * 10 * Time.ns)
            u.wDatapump.ack._ag.data.append(_id)
            addSize(17)
            u.wDatapump.ack._ag.data.append(_id)
            
        self.procs.append(itemsWithDelay)
        
        self.doSim(80 * 10 * Time.ns)
        
        self.assertEqual(len(u.items._ag.data), 0)
        
        req = u.wDatapump.req._ag.data
        self.assertEqual(len(req), 2)
        for i, _req in enumerate(req):
            self.assertValSequenceEqual(_req, [3, 0x1230 + i * 8, 0, 0])
        
        w = u.wDatapump.w._ag.data
        self.assertEqual(len(w), 2)
        for i, _w in enumerate(w):
            self.assertValSequenceEqual(_w, [16 + i, 255, 1])
    
        self.assertValEqual(self.model.uploadedCntr, 2)
    
       
    
    def test_timeoutWithMore(self):
        u = self.u
        _id = evalParam(u.ID).val
        
        u.items._ag.data.extend([16, 28, 99])
        u.baseAddr._ag.dout.append(0x1230)
        
        u.wDatapump.ack._ag.data.extend([NOP for _ in range(32 + 3 * 2)])
        u.wDatapump.ack._ag.data.append(_id)
        
        
        self.doSim(70 * 10 * Time.ns)
        self.assertEqual(len(u.items._ag.data), 0)
        req = u.wDatapump.req._ag.data
        self.assertEqual(len(req), 1)
        self.assertValSequenceEqual(req[0], [_id, 0x1230, 2, 0])
        
        w = u.wDatapump.w._ag.data
        self.assertEqual(len(w), 3)
        self.assertValSequenceEqual(w[0], [16, 255, 0])
        self.assertValSequenceEqual(w[1], [28, 255, 0])
        self.assertValSequenceEqual(w[2], [99, 255, 1])
        
        self.assertEqual(len(u.wDatapump.ack._ag.data), 0)
        
        self.assertValEqual(self.u.uploaded._ag.data[-1], 3)
        
    
    def test_fullFill(self):
        u = self.u
        N = 16
        _id = evalParam(u.ID).val

        u.baseAddr._ag.dout.append(0x1230)
        u.items._ag.data.extend([88 for _ in range(N)])
        u.wDatapump.ack._ag.data.extend([NOP for _ in range(N * 2)] + [_id, ])
        
        self.doSim(40 * 10 * Time.ns)
        
        self.assertEqual(len(u.items._ag.data), 0)
        
        req = u.wDatapump.req._ag.data
        self.assertEqual(len(req), 1)
        self.assertValSequenceEqual(req[0],
                                 [_id, 0x1230, N - 1, 0])
        w = u.wDatapump.w._ag.data
        self.assertEqual(len(w), N)
        for i, d in enumerate(w):
            self.assertValSequenceEqual(d, [88, 255, int(i == 15)])
        
        self.assertEqual(len(u.wDatapump.ack._ag.data), 0)
        
        self.assertValEqual(self.u.uploaded._ag.data[-1], N)
    
    def test_fullFill_randomized(self):
        u = self.u
        N = 16
        _id = evalParam(u.ID).val
        randomize = self.randomize
        
        randomize(u.items)
        randomize(u.wDatapump.w)
        randomize(u.wDatapump.req)
        randomize(u.wDatapump.ack)
        
        
        u.baseAddr._ag.dout.append(0x1230)
        u.items._ag.data.extend([88 for _ in range(2 * N - 1)])
        u.wDatapump.ack._ag.data.extend([NOP for _ in range(N * 2)] + [_id, ])
        
        self.doSim(80 * 10 * Time.ns)
        
        self.assertEqual(len(u.items._ag.data), 0)
        
        req = u.wDatapump.req._ag.data
        self.assertEqual(len(req), 1)
        self.assertValSequenceEqual(req[0],
                                 [_id, 0x1230, N - 1, 0])
        w = u.wDatapump.w._ag.data
        self.assertEqual(len(w), N)
        for i, d in enumerate(w):
            self.assertValSequenceEqual(d, [88, 255, int(i == 15)])
        
        self.assertEqual(len(u.wDatapump.ack._ag.data), 0)
        
        self.assertValEqual(self.u.uploaded._ag.data[-1], N)
        
    def test_fullFill_randomized2(self):
        u = self.u
        N = 16
        _id = evalParam(u.ID).val
        randomize = self.randomize

        u.baseAddr._ag.dout.append(0x1230)
        u.items._ag.data.extend([1 + i for i in range(N)])
        u.wDatapump.ack._ag.data.extend([NOP for _ in range(N * 2)] + [_id, ])
        
        
        randomize(u.wDatapump.w)
        randomize(u.items)
        randomize(u.wDatapump.req)
        randomize(u.wDatapump.ack)
        
        
        self.doSim(80 * 10 * Time.ns)
        
        self.assertEqual(len(u.items._ag.data), 0)
        
        req = u.wDatapump.req._ag.data
        self.assertEqual(len(req), 1)
        self.assertValSequenceEqual(req[0],
                                 [_id, 0x1230, N - 1, 0])
        w = u.wDatapump.w._ag.data
        self.assertEqual(len(w), N)
        self.assertEqual(len(u.wDatapump.ack._ag.data), 0)
        
        self.assertValEqual(self.u.uploaded._ag.data[-1], N) 
    
    def test_fullFill_randomized3(self):
        u = self.u
        BASE = 0x1230
        ITEMS = evalParam(u.SIZE_BLOCK_ITEMS).val
        N = ITEMS+10
        _id = evalParam(u.ID).val
        randomize = self.randomize

        u.baseAddr._ag.dout.append(BASE)
        for i in range(N):
            u.items._ag.data.append(1 + i)
            
        for _ in range(ceil(N / 16)):
            u.wDatapump.ack._ag.data.append(_id)
        
        def enReq(s):
            u.wDatapump.req._ag.enable = False
            yield s.wait(40*10* Time.ns)
            yield from agent_randomize(u.wDatapump.req._ag)(s)
        
        self.procs.append(enReq)
        
        randomize(u.wDatapump.w)
        randomize(u.items)
        #randomize(u.req)
        randomize(u.wDatapump.ack)
        
        
        self.doSim(N * 30 * Time.ns)
        
        self.assertEqual(len(u.items._ag.data), 0)
        
        req = u.wDatapump.req._ag.data
        self.assertEqual(len(req), ceil(N / 16))
        for i, _req in enumerate(req):
            addr = BASE + ((i * 16 * 8) % (ITEMS*8))
            if (1+i)*16 > N:
                l =  N - i*16
            else:
                l = 16
            self.assertValSequenceEqual(_req,
                                 [_id, addr, l-1, 0])
        w = u.wDatapump.w._ag.data
        self.assertEqual(len(w), N)
        self.assertEqual(len(u.wDatapump.ack._ag.data), 0)
        
        self.assertValEqual(self.u.uploaded._ag.data[-1], N) 
                
if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(Size2Mem_TC('test_fullFill_randomized3'))
    suite.addTest(unittest.makeSuite(ArrayBuff_writer_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

