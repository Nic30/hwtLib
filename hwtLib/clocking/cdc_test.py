#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwtLib.clocking.cdc import Cdc
from hwt.simulator.simTestCase import SimTestCase
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer, WaitWriteOnly, WaitCombRead


class CdcTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = u = Cdc()
        u.DATA_WIDTH = 32
        cls.compileSim(u)

    def runSim(self, dataInStimul, until=10 * CLK_PERIOD):
        collected = []
        u = self.u
        self.u.dataOut_clk._ag.period = CLK_PERIOD // 4
        self.u.dataOut_rst._ag.initDelay =\
            self.u.dataIn_rst._ag.initDelay = CLK_PERIOD * 2

        def dataCollector():
            # random small value to collect data after it is set
            yield Timer(CLK_PERIOD + 1)
            while True:
                yield WaitCombRead()
                d = u.dataOut.read()
                collected.append(d)
                yield Timer(CLK_PERIOD)

        self.procs.extend(
            [dataCollector(),
             dataInStimul()])
        super(CdcTC, self).runSim(until=until)
        return collected

    def test_normalOp(self):
        u = self.u
        u.dataIn._ag = None
        u.dataOut._ag = None
        expected = [0, 0, None, 0, 1, 2, 3, 4, 5]

        def dataInStimul():
            yield Timer(3 * CLK_PERIOD)
            for i in range(127):
                yield WaitWriteOnly()
                u.dataIn.write(i)
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
                u.dataIn.write(None)

        collected = self.runSim(dataInStimul)
        self.assertValSequenceEqual(collected, expected)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(CdcTC('test_invalidData'))
    suite.addTest(unittest.makeSuite(CdcTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
