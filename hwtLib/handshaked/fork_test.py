#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.interfaces.std import Handshaked
from hdl_toolkit.simulator.agentConnector import agInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hdl_toolkit.simulator.utils import agent_randomize
from hwtLib.handshaked.fork import HandshakedFork


class ForkTC(unittest.TestCase):
    def setUp(self):
        self.u = HandshakedFork(Handshaked)
        self.u.DATA_WIDTH.set(4)
        _, self.model, self.procs = simPrepare(self.u)
    
    def doSim(self, name, time=80 * Time.ns):
        simUnitVcd(self.model, self.procs,
                    "tmp/hsFork_" + name + ".vcd",
                    time=time)
    
    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

        self.doSim("passdata", 120 * Time.ns)

        collected0 = agInts(u.dataOut[0])
        collected1 = agInts(u.dataOut[1])
        
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], collected0)
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], collected1)
        
        self.assertSequenceEqual([], u.dataIn._ag.data)

class Fork_randomized_TC(ForkTC):
    def setUp(self):
        super(Fork_randomized_TC, self).setUp()
        self.procs.append(agent_randomize(self.u.dataIn._ag))
        
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(Fork_randomized_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
