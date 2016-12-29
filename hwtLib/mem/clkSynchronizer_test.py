#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.simulator.agentConnector import valuesToInts
from hwt.simulator.shortcuts import simUnitVcd, oscilate, pullDownAfter, \
    toSimModel, reconectUnitSignalsToModel
from hwtLib.mem.clkSynchronizer import ClkSynchronizer


CLK_PERIOD = 10 * Time.ns
        
class ClkSynchronizerTC(unittest.TestCase):
    def setUp(self):
        u = ClkSynchronizer()
        u.DATA_TYP = vecT(32)
        modelCls = toSimModel(u)
        reconectUnitSignalsToModel(u, modelCls)
        model = modelCls()
        
        self.u = u
        self.model = model
    
    def doSim(self, dataInStimul, name, time=100 * Time.ns): 
        collected = []
        u = self.u
                
        def dataCollector(s):
            yield s.wait(CLK_PERIOD + 0.001)  # random small value to collect data after it is set
            while True:
                d = s.read(u.outData)
                collected.append(d)
                yield s.wait(CLK_PERIOD)
        
        simUnitVcd(self.model, [oscilate(u.inClk, CLK_PERIOD),
                       oscilate(u.outClk, CLK_PERIOD, initWait=CLK_PERIOD / 4),
                       pullDownAfter(u.rst, CLK_PERIOD * 2),
                       dataCollector,
                       dataInStimul], "tmp/clkSynchronizer_" + name + ".vcd", time=100 * Time.ns)   
        return collected
    
    def test_normalOp(self):
        u = self.u

        expected = [0, 0, 0, None, 0, 1, 2, 3, 4]
        
        def dataInStimul(s):
            yield s.wait(3 * CLK_PERIOD)
            for i in range(127):
                s.write(i, u.inData)
                yield s.wait(CLK_PERIOD)
                
        collected = self.doSim(dataInStimul, "normalOp")
        self.assertSequenceEqual(expected, valuesToInts(collected))

    def test_invalidData(self):
        u = self.u
    
        CLK_PERIOD = 10 * Time.ns
        expected = [0, 0, 0, None, None, None, None, None, None]
        
        def dataInStimul(s):
            yield s.wait(3 * CLK_PERIOD)
            for _ in range(127):
                yield s.wait(CLK_PERIOD)
                s.write(None, u.inData)
        
        collected = self.doSim(dataInStimul, "invalidData")
        self.assertSequenceEqual(expected, valuesToInts(collected))

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(ClkSynchronizerTC('test_invalidData'))
    suite.addTest(unittest.makeSuite(ClkSynchronizerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
