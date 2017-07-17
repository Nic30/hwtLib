#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.joinPrioritized import HsJoinPrioritized


class HsJoinWithReference(HsJoinPrioritized):
    def _declr(self):
        HsJoinPrioritized._declr(self)
        addClkRstn(self)


class HsJoinPrioritizedTC(SimTestCase):
    def setUp(self):
        super(HsJoinPrioritizedTC, self).setUp()
        self.u = HsJoinWithReference(Handshaked)
        self.u.DATA_WIDTH.set(8)
        self.prepareUnit(self.u)

    def test_passdata(self):
        u = self.u

        u.dataIn[0]._ag.data.extend([1, 2, 3, 4, 5, 6])
        u.dataIn[1]._ag.data.extend([7, 8, 9, 10, 11, 12])

        self.doSim(300 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

        for d in u.dataIn:
            self.assertEmpty(d._ag.data)


class HsJoinPrioritized_randomized_TC(HsJoinPrioritizedTC):
    def setUp(self):
        super(HsJoinPrioritized_randomized_TC, self).setUp()
        #self.procs.append(agent_randomize(self.u.dataIn[0]._ag))
        #self.procs.append(agent_randomize(self.u.dataIn[1]._ag))
        self.randomize(self.u.dataOut)

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(HsJoinPrioritized_randomized_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
