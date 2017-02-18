#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.structManipulators.arrayItemGetter import ArrayItemGetter
from hwtLib.abstract.denseMemory import DenseMemory


class ArrayItemGetterTC(SimTestCase):
    def setUp(self):
        u = self.u = ArrayItemGetter()
        self.ID = 3
        u.ID.set(self.ID)

        self.ITEMS = 32
        u.ITEMS.set(self.ITEMS)
        
        self.DATA_WIDTH = 64
        u.DATA_WIDTH.set(self.DATA_WIDTH)
        
        self.ITEM_WIDTH = 64
        u.ITEM_WIDTH.set(self.ITEM_WIDTH)
        
        
        _, self.model, self.procs = simPrepare(self.u)
    
    
    def test_nop(self):
        u = self.u
        self.doSim(200 * Time.ns)
        
        self.assertEqual(len(u.rDatapump.req._ag.data), 0)
        self.assertEqual(len(u.item._ag.data), 0)
    
    def test_singleGet(self):
        u = self.u
        t = 5
        BASE = 8 * (self.DATA_WIDTH // 8)
        MAGIC = 99
        INDEX = self.ITEMS - 1
        
        u.base._ag.data.append(BASE)
        u.index._ag.data.append(INDEX)
        
        m = DenseMemory(self.DATA_WIDTH, u.clk, rDatapumpIntf=u.rDatapump)
        m.data[BASE // 8 + INDEX] = MAGIC
        
        self.doSim(t * 10 * Time.ns)
        
        self.assertEqual(len(u.item._ag.data), 1)
        self.assertValEqual(u.item._ag.data[0], MAGIC)
        
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(ArrayItemGetterTC('test_downloadFullBlockRandomized'))
    suite.addTest(unittest.makeSuite(ArrayItemGetterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

