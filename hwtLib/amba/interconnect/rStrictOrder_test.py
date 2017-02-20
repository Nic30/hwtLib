#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import agent_randomize
from hwt.synthesizer.param import evalParam
from hwtLib.abstract.denseMemory import DenseMemory
from hwtLib.amba.interconnect.rStricOrder import RStrictOrderInterconnect
from hwt.bitmask import mask


class RStrictOrderInterconnectTC(SimTestCase):
    def setUp(self):
        self.u = RStrictOrderInterconnect()
        self.MAX_TRANS_OVERLAP = evalParam(self.u.MAX_TRANS_OVERLAP).val
        self.DATA_WIDTH = evalParam(self.u.DATA_WIDTH).val
        _, self.model, self.procs = simPrepare(self.u)
    
    
    def test_nop(self):
        u = self.u
        self.doSim(200 * Time.ns)
        
        for d in u.drivers:
            self.assertEqual(len(d.r._ag.data), 0)
        
        self.assertEqual(len(u.rDatapump.req._ag.data), 0)
    
    def test_passWithouData(self):
        u = self.u
        
        for i, driver in enumerate(u.drivers):
            driver.req._ag.data.append((i + 1, i + 1, i + 1, 0))
        
        self.doSim(40 * Time.ns)
        
        for d in u.drivers:
            self.assertEqual(len(d.r._ag.data), 0)
        
        self.assertEqual(len(u.rDatapump.req._ag.data), 2)
        for i, req in enumerate(u.rDatapump.req._ag.data):
            self.assertValSequenceEqual(req,
                                        (i + 1, i + 1, i + 1, 0))
    def test_passWithData(self):
        u = self.u
        
        for i, driver in enumerate(u.drivers):
            _id = i + 1
            _len = i + 1
            driver.req._ag.data.append((_id, i + 1, _len, 0))
            for i2 in range(_len + 1):
                u.rDatapump.r._ag.data.append((_id, i + 1, mask(self.DATA_WIDTH), i2 == _len))
                
        self.doSim(200 * Time.ns)
        
        for i, d in enumerate(u.drivers):
            self.assertEqual(len(d.r._ag.data), i + 1 + 1)
        
        self.assertEqual(len(u.rDatapump.req._ag.data), 2)
        for i, req in enumerate(u.rDatapump.req._ag.data):
            self.assertValSequenceEqual(req,
                                        (i + 1, i + 1, i + 1, 0))
   

    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_measuringFifoTC('test_withSizeBrake'))
    suite.addTest(unittest.makeSuite(RStrictOrderInterconnectTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

