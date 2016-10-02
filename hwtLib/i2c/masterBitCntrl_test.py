#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.simulator.shortcuts import simPrepare, simUnitVcd
from hwtLib.i2c.masterBitCntrl import I2cMasterBitCtrl


class I2CMasterBitCntrlTC(unittest.TestCase):
    def setUp(self):
        u = I2cMasterBitCtrl()
        self.u, self.model, self.procs = simPrepare(u)
        

    def testNop(self):
        u = self.u
        u.clk_cnt_initVal._ag.data = [4]
    
    
    def runSim(self, name, time=1 * Time.ms):
        simUnitVcd(self.model, self.procs,
                   "tmp/i2cm_bitcntrl_" + name + ".vcd", time=time)
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(I2CMasterBitCntrlTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)