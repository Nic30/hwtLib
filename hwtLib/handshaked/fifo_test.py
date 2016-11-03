#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.interfaces.std import Handshaked
from hdl_toolkit.simulator.agentConnector import agInts, valuesToInts, valToInt
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hdl_toolkit.simulator.utils import agent_randomize
from hwtLib.handshaked.fifo import HandshakedFifo


class HsFifoTC(unittest.TestCase):
    def setUp(self):
        self.u = HandshakedFifo(Handshaked)
        self.u.DEPTH.set(8)
        self.u.DATA_WIDTH.set(4)
        _, self.model, self.procs = simPrepare(self.u)
    
    def getTestName(self):
        className, testName = self.id().split(".")[-2:]
        return "%s_%s" % (className, testName)
    
    def doSim(self, time):
        simUnitVcd(self.model, self.procs,
                    "tmp/" + self.getTestName() + ".vcd",
                    time=time)
    
    def test_stuckedData(self):
        u = self.u
        u.dataIn._ag.data = [1]

        u.dataOut._ag.enable = False
        self.doSim(120 * Time.ns)
        self.assertEqual(valToInt(self.model.dataOut_data._val), 1)
        
        
        
    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

        self.doSim(120 * Time.ns)
        
        collected0 = valuesToInts(u.dataOut._ag.data)
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], collected0)
        
        self.assertSequenceEqual([], u.dataIn._ag.data)

class HsFifo_randomized_TC(HsFifoTC):
    def setUp(self):
        super(HsFifo_randomized_TC, self).setUp()
        self.procs.append(agent_randomize(self.u.dataIn._ag))
        self.procs.append(agent_randomize(self.u.dataOut._ag))
        
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(HsFifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
