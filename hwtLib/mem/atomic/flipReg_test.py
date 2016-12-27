#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import valuesToInts
from hwt.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.mem.atomic.flipReg import FlipRegister


class FlipRegTC(unittest.TestCase):
    def setUp(self):
        self.u, self.model, self.procs = simPrepare(FlipRegister())
        
    def runSim(self, name, time=90 * Time.ns):
        simUnitVcd(self.model, self.procs,
                "tmp/flipReg_%s.vcd" % name,
                time=90 * Time.ns)
    
    def test_simpleWriteAndSwitch(self):
        u = self.u
        
        # u.select_sig._ag.initDelay = 6 * Time.ns
        u.select_sig._ag.data = [0, 0, 0, 0, 1, 0]
        u.first._ag.dout = [1]
        u.second._ag.dout = [2]
        
        self.runSim("simpleWriteAndSwitch")

        self.assertSequenceEqual([0, 0, 1, 1, 2, 1, 1, 1, 1], valuesToInts(u.first._ag.din))
        self.assertSequenceEqual([0, 0, 2, 2, 1, 2, 2, 2, 2], valuesToInts(u.second._ag.din))

    
    
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(FlipRegTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
