#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import Handshaked
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import agent_randomize
from hwtLib.handshaked.joinFair import HsJoinFairShare


class HsJoinFairTC(SimTestCase):
    def setUp(self):
        self.u = HsJoinFairShare(Handshaked)
        self.u.DATA_WIDTH.set(8)
        _, self.model, self.procs = simPrepare(self.u)
    
    def test_passdata(self):
        u = self.u

        u.dataIn[0]._ag.data = [1, 2, 3, 4, 5, 6]
        u.dataIn[1]._ag.data = [7, 8, 9, 10, 11, 12]

        expected = []
        for d0, d1 in zip(u.dataIn[0]._ag.data, u.dataIn[1]._ag.data):
            expected.extend([d0, d1])
            
        self.doSim(300 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data, expected)
        
        self.assertSequenceEqual([], u.dataIn[0]._ag.data)
        self.assertSequenceEqual([], u.dataIn[1]._ag.data)

    def test_passdata2(self):
        u = self.u

        u.dataIn[0]._ag.data = [1, 2, 3]
        u.dataIn[1]._ag.data = [4, 5, 6]

        expected = []
        for d0, d1 in zip(u.dataIn[0]._ag.data, u.dataIn[1]._ag.data):
            expected.extend([d0, d1])
        
        d = [7, 8, 9, 10, 11, 12]
        u.dataIn[1]._ag.data.extend(d)
        expected.extend(d)
        
        self.doSim(300 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data, expected)
        
        self.assertSequenceEqual([], u.dataIn[0]._ag.data)
        self.assertSequenceEqual([], u.dataIn[1]._ag.data)


#class HsJoin_randomized_TC(HsJoinTC):
#    def setUp(self):
#        super(HsJoin_randomized_TC, self).setUp()
#        #self.procs.append(agent_randomize(self.u.dataIn[0]._ag))
#        #self.procs.append(agent_randomize(self.u.dataIn[1]._ag))
#        self.procs.append(agent_randomize(self.u.dataOut._ag))
#        
        
if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(HsJoinFairTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
