#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.interfaces.std import FifoReader, FifoWriter
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit
from hwtLib.mem.fifo import Fifo


class FifoReaderPassTrought(Unit):
    def _declr(self):
        addClkRstn(self)
        self.din = FifoReader()
        self.dout = FifoReader()

    def _impl(self):
        self.dout(self.din)


class FifoWriterPassTrought(FifoReaderPassTrought):
    def _declr(self):
        addClkRstn(self)
        self.din = FifoWriter()
        self.dout = FifoWriter()


class FifoAgentsTC(SimTestCase):
    def test_fifoReader(self):
        u = FifoReaderPassTrought()

        self.prepareUnit(u)
        self.randomize(u.din)
        self.randomize(u.dout)

        ref = [i for i in range(30)]
        u.din._ag.data.extend(ref)
        self.runSim(120 * 10 * Time.ns)

        self.assertValSequenceEqual(u.dout._ag.data, ref)

    def test_fifoWriter(self):
        u = FifoWriterPassTrought()

        self.prepareUnit(u)
        self.randomize(u.din)
        self.randomize(u.dout)

        ref = [i for i in range(30)]
        u.din._ag.data.extend(ref)
        self.runSim(120 * 10 * Time.ns)

        self.assertValSequenceEqual(u.dout._ag.data, ref)


class FifoTC(SimTestCase):
    def setUp(self):
        u = self.u = Fifo()
        u.DATA_WIDTH.set(8)
        u.DEPTH.set(4)
        u.EXPORT_SIZE.set(True)
        self.prepareUnit(u)

    def getTime(self, wordCnt):
        return wordCnt * 10 * Time.ns

    def test_fifoSingleWord(self):
        u = self.u

        expected = [1]
        u.dataIn._ag.data.extend(expected)

        self.runSim(90 * Time.ns)

        collected = u.dataOut._ag.data

        self.assertValSequenceEqual(collected, expected)

    def test_fifoWriterDisable(self):
        u = self.u

        data = [1, 2, 3, 4]
        u.dataIn._ag.data.extend(data)
        u.dataIn._ag._enabled = False

        self.runSim(self.getTime(8))

        self.assertValSequenceEqual(u.dataOut._ag.data, [])
        self.assertValSequenceEqual(u.dataIn._ag.data, data)

    def test_normalOp(self):
        u = self.u

        expected = list(range(4))
        u.dataIn._ag.data.extend(expected)

        self.runSim(self.getTime(9))

        self.assertValSequenceEqual(u.dataOut._ag.data, expected)

    def test_multiple(self):
        u = self.u
        u.dataOut._ag._enabled = False

        def openOutput(sim):
            yield sim.wait(self.getTime(9))
            u.dataOut._ag.setEnable(True, sim)
        self.procs.append(openOutput)

        expected = list(range(2 * 8))
        u.dataIn._ag.data.extend(expected)

        self.runSim(self.getTime(26))

        collected = u.dataOut._ag.data
        if u.EXPORT_SIZE:
            self.assertValSequenceEqual(u.size._ag.data,
                [0, 1, 2, 3, 4, 4, 4, 4, 4,
                 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 1, 0])

        self.assertValSequenceEqual(collected, expected)

    def test_tryMore(self):
        u = self.u

        u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])
        u.dataOut._ag._enabled = False

        self.runSim(self.getTime(12))

        collected = u.dataOut._ag.data

        self.assertValSequenceEqual(self.model.memory._val, [1, 2, 3, 4])
        self.assertValSequenceEqual(collected, [])
        self.assertValSequenceEqual(u.dataIn._ag.data, [5, 6])

    def test_tryMore2(self):
        u = self.u

        u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6, 7, 8])

        def closeOutput(sim):
            yield sim.wait(self.getTime(4))
            u.dataOut._ag.setEnable(False, sim)

        self.procs.append(closeOutput)
        self.runSim(self.getTime(15))

        collected = u.dataOut._ag.data

        self.assertValSequenceEqual(self.model.memory._val.val, [5, 6, 3, 4])
        self.assertSequenceEqual(collected, [1, 2])
        self.assertSequenceEqual(u.dataIn._ag.data, [7, 8])

    def test_doloop(self):
        u = self.u
        u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])

        self.runSim(self.getTime(12))

        collected = u.dataOut._ag.data

        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], collected)
        self.assertSequenceEqual([], u.dataIn._ag.data)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(FifoTC('test_multiple'))
    suite.addTest(unittest.makeSuite(FifoAgentsTC))
    suite.addTest(unittest.makeSuite(FifoTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
