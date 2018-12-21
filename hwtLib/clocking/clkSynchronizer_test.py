#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.types.bits import Bits
from hwt.simulator.agentConnector import valuesToInts
from hwtLib.clocking.clkSynchronizer import ClkSynchronizer
from hwt.simulator.simTestCase import SimTestCase
from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer


class ClkSynchronizerTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        super(ClkSynchronizerTC, cls).setUpClass()
        u = ClkSynchronizer()
        u.DATA_TYP = Bits(32)
        cls.prepareUnit(u)

    def setUp(self):
        super(SimTestCase, self).setUp()
        self.restartSim()

    def runSim(self, dataInStimul, until=10 * CLK_PERIOD):
        collected = []
        u = self.u
        self.u.outClk._ag.period = CLK_PERIOD // 4
        self.u.rst._ag.initDelay = CLK_PERIOD * 2

        def dataCollector(s):
            # random small value to collect data after it is set
            yield Timer(CLK_PERIOD + 0.001)
            while True:
                d = u.outData.read()
                collected.append(d)
                yield Timer(CLK_PERIOD)

        self.procs.extend(
            [dataCollector,
             dataInStimul])
        super(ClkSynchronizerTC, self).runSim(until=until)
        return collected

    def test_normalOp(self):
        u = self.u

        expected = [0, 0, 0, None, 0, 1, 2, 3, 4]

        def dataInStimul(s):
            yield Timer(3 * CLK_PERIOD)
            for i in range(127):
                u.inData.write(i)
                yield Timer(CLK_PERIOD)

        collected = self.runSim(dataInStimul)
        self.assertSequenceEqual(expected, valuesToInts(collected))

    def test_invalidData(self):
        u = self.u

        expected = [0, 0, 0, None, None, None, None, None, None]

        def dataInStimul(s):
            yield Timer(3 * CLK_PERIOD)
            for _ in range(127):
                yield Timer(CLK_PERIOD)
                u.inData.write(None)

        collected = self.runSim(dataInStimul)
        self.assertSequenceEqual(expected, valuesToInts(collected))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(ClkSynchronizerTC('test_invalidData'))
    suite.addTest(unittest.makeSuite(ClkSynchronizerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
