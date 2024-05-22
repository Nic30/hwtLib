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
        cls.dut = dut = Cdc()
        dut.DATA_WIDTH = 32
        cls.compileSim(dut)

    def runSim(self, dataInStimul, until=10 * CLK_PERIOD):
        collected = []
        dut = self.dut
        self.dut.dataOut_clk._ag.period = CLK_PERIOD // 4
        self.dut.dataOut_rst._ag.initDelay =\
            self.dut.dataIn_rst._ag.initDelay = CLK_PERIOD * 2

        def dataCollector():
            # random small value to collect data after it is set
            yield Timer(CLK_PERIOD + 1)
            while True:
                yield WaitCombRead()
                d = dut.dataOut.read()
                collected.append(d)
                yield Timer(CLK_PERIOD)

        self.procs.extend(
            [dataCollector(),
             dataInStimul()])
        super(CdcTC, self).runSim(until=until)
        return collected

    def test_normalOp(self):
        dut = self.dut
        dut.dataIn._ag = None
        dut.dataOut._ag = None
        expected = [0, 0, None, 0, 1, 2, 3, 4, 5]

        def dataInStimul():
            yield Timer(3 * CLK_PERIOD)
            for i in range(127):
                yield WaitWriteOnly()
                dut.dataIn.write(i)
                yield Timer(CLK_PERIOD)

        collected = self.runSim(dataInStimul)
        self.assertValSequenceEqual(collected, expected)

    def test_invalidData(self):
        dut = self.dut

        expected = [0, 0, None, None, None, None, None, None, None]

        def dataInStimul():
            yield Timer(3 * CLK_PERIOD)
            for _ in range(127):
                yield Timer(CLK_PERIOD)
                yield WaitWriteOnly()
                dut.dataIn.write(None)

        collected = self.runSim(dataInStimul)
        self.assertValSequenceEqual(collected, expected)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([CdcTC("test_invalidData")])
    suite = testLoader.loadTestsFromTestCase(CdcTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
