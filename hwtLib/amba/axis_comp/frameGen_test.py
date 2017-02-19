#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.frameGen import AxisFrameGen


class AxisFrameGenTC(SimTestCase):
    def setUp(self):
        self.u = AxisFrameGen()
        _, self.model, self.procs = simPrepare(self.u)
    
    def wReg(self, addr, val):  
        aw = self.u.cntrl._ag.aw.data
        w = self.u.cntrl._ag.w.data 
        aw.append(addr)
        w.append((val, mask(4)))
    
    def test_len0(self):
        u = self.u
        self.wReg(0x4, 0)
        self.wReg(0x0, 1)



        # u.dataOut._ag.enable = False
        self.doSim(120 * Time.ns)
        self.assertValSequenceEqual(u.axis_out._ag.data,
                        [[0, mask(8), 1] for _ in range(6)])
        
    def test_len1(self):
        u = self.u
        L = 1
        self.wReg(0x4, L)
        self.wReg(0x0, 1)


        # u.dataOut._ag.enable = False
        self.doSim(120 * Time.ns)
        # self.assertValEqual(self.model.dataOut_data, 1)
        self.assertValSequenceEqual(u.axis_out._ag.data,
                        [[ L - (i % (L + 1)), mask(8), int((i % (L + 1)) >= L)] for i in range(6)])

    def test_len4(self):
        u = self.u
        L = 4
        self.wReg(0x4, L)
        self.wReg(0x0, 1)



        # u.dataOut._ag.enable = False
        self.doSim(120 * Time.ns)
        # self.assertValEqual(self.model.dataOut_data, 1)
        self.assertValSequenceEqual(u.axis_out._ag.data,
                        [[ L - (i % (L + 1)), mask(8), int((i % (L + 1)) >= L)] for i in range(6)])
                

        
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(AxisFrameGenTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
