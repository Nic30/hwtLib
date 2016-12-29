#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.i2c.masterBitCntrl import I2cMasterBitCtrl


class I2CMasterBitCntrlTC(SimTestCase):
    def setUp(self):
        u = I2cMasterBitCtrl()
        self.u, self.model, self.procs = simPrepare(u)
        

    def testNop(self):
        u = self.u
        u.clk_cnt_initVal._ag.data = [4]
        self.doSim(10 * 10 * Time.ns)
    
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(I2CMasterBitCntrlTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
