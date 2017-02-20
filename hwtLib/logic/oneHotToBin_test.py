#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.logic.oneHotToBin import OneHotToBin


class OneHotToBinSimWrap(OneHotToBin):
    def _declr(self):
        OneHotToBin._declr(self)
        addClkRstn(self)

class OneHotToBinTC(SimTestCase):
    LEN_MAX = 255
    
    def setUp(self):
        u = OneHotToBinSimWrap()
        self.ONE_HOT_WIDTH = 8
        u.ONE_HOT_WIDTH.set(self.ONE_HOT_WIDTH)
        self.u, self.model, self.procs = simPrepare(u)
    
    def test_nop(self):
        u = self.u
        oneHot = u.oneHot._ag.data
        oneHot.append(0)
        
        self.doSim(4 * 10 * Time.ns)
        
        self.assertValSequenceEqual(u.bin._ag.data,[])
        
    def test_basic(self):
        u = self.u
        oneHot = u.oneHot._ag.data
        oneHot.append(0)
        for i in range(self.ONE_HOT_WIDTH):
            oneHot.append(1 << i)  
        oneHot.append(0)
        
        self.doSim((self.ONE_HOT_WIDTH + 3) * 10 * Time.ns)
        
        self.assertValSequenceEqual(u.bin._ag.data, range(self.ONE_HOT_WIDTH))
    
      
   
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(OneHotToBinTC('test_basic'))
    suite.addTest(unittest.makeSuite(OneHotToBinTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    
