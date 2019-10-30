#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.types.bits import Bits
from hwtLib.clocking.clkSynchronizer import ClkSynchronizer
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer, WaitWriteOnly, WaitCombRead


class ClkSynchronizerTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = u = ClkSynchronizer()
        u.DATA_TYP = Bits(32)
        return u

    def runSim(self, dataInStimul, until=10 * CLK_PERIOD):
        collected = []
        u = self.u
        self.u.outClk._ag.period = CLK_PERIOD // 4
        self.u.rst._ag.initDelay = CLK_PERIOD * 2

        def dataCollector():
            # random small value to collect data after it is set
            yield Timer(CLK_PERIOD + 0.001)
            while True:
                yield WaitCombRead()
                d = u.outData.read()
                collected.append(d)
                yield Timer(CLK_PERIOD)

        self.procs.extend(
            [dataCollector(),
             dataInStimul()])
        super(ClkSynchronizerTC, self).runSim(until=until)
        return collected

    def test_normalOp(self):
        u = self.u
        u.inData._ag = None
        u.outData._ag = None
        expected = [0, 0, None, 0, 1, 2, 3, 4, 5]

        def dataInStimul():
            yield Timer(3 * CLK_PERIOD)
            for i in range(127):
                yield WaitWriteOnly()
                u.inData.write(i)
                yield Timer(CLK_PERIOD)

        collected = self.runSim(dataInStimul)
        self.assertValSequenceEqual(collected, expected)

    def test_invalidData(self):
        u = self.u

        expected = [0, 0, None, None, None, None, None, None, None]

        def dataInStimul():
            yield Timer(3 * CLK_PERIOD)
            for _ in range(127):
                yield Timer(CLK_PERIOD)
                yield WaitWriteOnly()
                u.inData.write(None)

        collected = self.runSim(dataInStimul)
        self.assertValSequenceEqual(collected, expected)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(ClkSynchronizerTC('test_invalidData'))
    suite.addTest(unittest.makeSuite(ClkSynchronizerTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
