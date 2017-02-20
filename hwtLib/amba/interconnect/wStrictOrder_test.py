#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import agent_randomize
from hwt.synthesizer.param import evalParam
from hwtLib.abstract.denseMemory import DenseMemory
from hwtLib.amba.interconnect.wStrictOrder import WStrictOrderInterconnect
from hwt.bitmask import mask


class WStrictOrderInterconnectTC(SimTestCase):
    def setUp(self):
        self.u = WStrictOrderInterconnect()
        self.MAX_TRANS_OVERLAP = evalParam(self.u.MAX_TRANS_OVERLAP).val
        self.DATA_WIDTH = evalParam(self.u.DATA_WIDTH).val
        
        self.DRIVER_CNT =  evalParam(self.u.DRIVER_CNT).val
        _, self.model, self.procs = simPrepare(self.u)
    
    
    def test_nop(self):
        u = self.u
        self.doSim(200 * Time.ns)
        
        for d in u.drivers:
            self.assertEqual(len(d.ack._ag.data), 0)
        
        self.assertEqual(len(u.wDatapump.req._ag.data), 0)
        self.assertEqual(len(u.wDatapump.w._ag.data), 0)
    
    def test_passReq(self):
        u = self.u
        
        for i, driver in enumerate(u.drivers):
            driver.req._ag.data.append((i + 1, i + 1, i + 1, 0))
        
        self.doSim(40 * Time.ns)
        
        self.assertEqual(len(u.wDatapump.w._ag.data), 0)
        
        req = u.wDatapump.req._ag.data
        self.assertEqual(len(req), 2)
        for i, _req in enumerate(req):
            self.assertValSequenceEqual(_req,
                                        (i + 1, i + 1, i + 1, 0))

    def test_passData(self):
        u = self.u
        
        for i, driver in enumerate(u.drivers):
            driver.req._ag.data.append((i + 1, i + 1, i + 1, 0))
            
            _data, strb, last = i +1, mask(self.DATA_WIDTH), 1
            driver.w._ag.data.append((_data, strb, last))
            
        self.doSim(80 * Time.ns)
        
        self.assertEqual(len(u.wDatapump.w._ag.data), self.DRIVER_CNT)
        
        req = u.wDatapump.req._ag.data
        self.assertEqual(len(req), 2)
        for i, _req in enumerate(req):
            self.assertValSequenceEqual(_req,
                                        (i + 1, i + 1, i + 1, 0))
        
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_measuringFifoTC('test_withSizeBrake'))
    suite.addTest(unittest.makeSuite(WStrictOrderInterconnectTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

