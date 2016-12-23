#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.specialValues import Time
from hwt.interfaces.std import Handshaked
from hwt.simulator.agentConnector import agInts
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.utils import agent_randomize
from hwtLib.handshaked.fork import HandshakedFork
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase


class HsForkWithReference(HandshakedFork):
    def _declr(self):
        HandshakedFork._declr(self)
        addClkRstn(self)

class HsForkTC(SimTestCase):
    def setUp(self):
        self.u = HsForkWithReference(Handshaked)
        self.u.DATA_WIDTH.set(4)
        _, self.model, self.procs = simPrepare(self.u)
    
    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

        self.doSim(120 * Time.ns)

        collected0 = agInts(u.dataOut[0])
        collected1 = agInts(u.dataOut[1])
        
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], collected0)
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], collected1)
        
        self.assertSequenceEqual([], u.dataIn._ag.data)

class HsFork_randomized_TC(HsForkTC):
    def setUp(self):
        super(HsFork_randomized_TC, self).setUp()
        self.procs.append(agent_randomize(self.u.dataIn._ag))
        
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(HsFork_randomized_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
