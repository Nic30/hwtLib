#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import copy
import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwt.simulator.agentConnector import valuesToInts
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.param import evalParam
from hwtLib.mem.fifo import Fifo


class FifoTC(SimTestCase):
    def setUp(self):
        self.u = Fifo()
        self.u.DATA_WIDTH.set(8)
        self.u.DEPTH.set(4)
        self.u.EXPORT_SIZE.set(True)
        _, self.model, self.procs = simPrepare(self.u)
    
    def test_fifoSingleWord(self):
        u = self.u
        
        expected = [1]
        u.dataIn._ag.data = copy(expected)

        self.doSim(90 * Time.ns)
        
        collected = u.dataOut._ag.data

        self.assertSequenceEqual(expected, valuesToInts(collected))
    
    def test_fifoWritterDisable(self):
        u = self.u
        
        data = [1, 2, 3, 4]
        u.dataIn._ag.data = copy(data)
        u.dataIn._ag.enable = False

        self.doSim(80 * Time.ns)
        
        self.assertSequenceEqual([], u.dataOut._ag.data)
        self.assertSequenceEqual(data, u.dataIn._ag.data)
        
        
    
    def test_normalOp(self):
        u = self.u
        
        expected = list(range(4))
        u.dataIn._ag.data = copy(expected)

        self.doSim(90 * Time.ns)
        
        collected = u.dataOut._ag.data
        self.assertSequenceEqual(expected, valuesToInts(collected))

    def test_multiple(self):
        u = self.u
        hasSize = evalParam(u.EXPORT_SIZE).val
        u.dataOut._ag.enable = False
        
        def openOutput(s):
            yield s.wait(9 * 10 * Time.ns)
            u.dataOut._ag.enable = True
        self.procs.append(openOutput)
            
        expected = list(range(2 * 8))
        u.dataIn._ag.data = copy(expected)

        self.doSim(260 * Time.ns)
        
        collected = u.dataOut._ag.data
        if hasSize:
            self.assertValSequenceEqual(u.size._ag.data,
                [0, 0, 1, 2, 3, 4, 4, 4, 4, 4,
                 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 1, 0])

        
        self.assertValSequenceEqual(collected, expected)


    def test_tryMore(self):
        u = self.u
        
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]
        u.dataOut._ag.enable = False
        
        self.doSim(120 * Time.ns)

        collected = agInts(u.dataOut)
        
        self.assertSequenceEqual([1, 2, 3, 4], valuesToInts(self.model.memory._val))
        self.assertSequenceEqual(collected, [])
        self.assertSequenceEqual(u.dataIn._ag.data, [5, 6])
        
    def test_tryMore2(self):
        u = self.u
        
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6, 7, 8]
        def closeOutput(s):
            yield s.wait(4 * 10 * Time.ns)
            u.dataOut._ag.enable = False
            
        self.procs.append(closeOutput)
        self.doSim(150 * Time.ns)

        collected = agInts(u.dataOut)
        
        self.assertValSequenceEqual(self.model.memory._val.val, [5, 6, 3, 4])
        self.assertSequenceEqual(collected, [1, 2])
        self.assertSequenceEqual(u.dataIn._ag.data, [7, 8])
             

    def test_doloop(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

        self.doSim(120 * Time.ns)

        collected = agInts(u.dataOut)
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], collected)
        self.assertSequenceEqual([], u.dataIn._ag.data)
    
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(FifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
