#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hdl_toolkit.interfaces.std import Handshaked
from hdl_toolkit.simulator.agentConnector import agInts
from hdl_toolkit.simulator.shortcuts import simUnitVcd, simPrepare
from hwtLib.handshaked.fork import HandshakedFork
from hdl_toolkit.hdlObjects.specialValues import Time


class ForkTC(unittest.TestCase):
    def setUp(self):
        u = HandshakedFork(Handshaked)
        u.DATA_WIDTH.set(4)
        self.u, self.model, self.procs = simPrepare(u)
    
    def doSim(self, name, time=80 * Time.ns):
        simUnitVcd(self.model, self.procs,
                    "tmp/hsFork_" + name + ".vcd",
                    time=time)
    
    def test_passdata(self):
        u = self.u
        u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

        self.doSim("passdata", 120 * Time.ns)

        collected = agInts(u.dataOut)
        self.assertSequenceEqual([17], collected)  # 1 was in reset
        self.assertSequenceEqual([2, 3, 4, 5, 6], u.dataIn._ag.data)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(ForkTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
