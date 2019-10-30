#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.interfaces.std import FifoReader, FifoWriter
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.unit import Unit
from hwtLib.mem.fifo import Fifo
from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer, WaitWriteOnly


class FifoReaderPassTrought(Unit):

    def _declr(self):
        addClkRstn(self)
        self.din = FifoReader()
        self.dout = FifoReader()._m()

    def _impl(self):
        self.dout(self.din)


class FifoWriterPassTrought(FifoReaderPassTrought):

    def _declr(self):
        addClkRstn(self)
        self.din = FifoWriter()
        self.dout = FifoWriter()._m()


class FifoReaderAgentTC(SingleUnitSimTestCase):
    CLK = CLK_PERIOD

    @classmethod
    def getUnit(cls):
        cls.u = FifoReaderPassTrought()
        return cls.u

    def test_fifoReader(self):
        u = self.u
        self.randomize(u.din)
        self.randomize(u.dout)

        ref = [i for i in range(30)]
        u.din._ag.data.extend(ref)
        self.runSim(120 * self.CLK)

        self.assertValSequenceEqual(u.dout._ag.data, ref)


class FifoWriterAgentTC(SingleUnitSimTestCase):
    CLK = CLK_PERIOD

    @classmethod
    def getUnit(cls):
        cls.u = FifoWriterPassTrought()
        return cls.u

    def test_fifoWriter(self):
        u = self.u

        self.randomize(u.din)
        self.randomize(u.dout)

        ref = [i for i in range(30)]
        u.din._ag.data.extend(ref)
        self.runSim(120 * self.CLK)

        self.assertValSequenceEqual(u.dout._ag.data, ref)


class FifoTC(SingleUnitSimTestCase):
    ITEMS = 4
    IN_CLK = CLK_PERIOD
    OUT_CLK = CLK_PERIOD
    CLK = max(IN_CLK, OUT_CLK)  # clock used for resolving of sim duration

    @classmethod
    def getUnit(cls):
        u = cls.u = Fifo()
        u.DATA_WIDTH = 8
        u.DEPTH = cls.ITEMS
        u.EXPORT_SIZE = True
        return u

    def getFifoItems(self):
        m = self.rtl_simulator.io.memory
        return set([int(x.read()) for x in m])

    def getUnconsumedInput(self):
        return self.u.dataIn._ag.data

    def test_fifoSingleWord(self):
        u = self.u

        expected = [1]
        u.dataIn._ag.data.extend(expected)

        self.runSim(9 * self.CLK)

        collected = u.dataOut._ag.data
        self.assertValSequenceEqual(collected, expected)

    def test_fifoWriterDisable(self):
        u = self.u

        ref = [i + 1 for i in range(self.ITEMS)]
        u.dataIn._ag.data.extend(ref)

        def init():
            u.dataIn._ag.setEnable(False)
            return
            yield

        self.procs.append(init())

        self.runSim(8 * self.CLK)

        self.assertValSequenceEqual(u.dataOut._ag.data, [])
        self.assertValSequenceEqual(self.getUnconsumedInput(), ref)

    def test_normalOp(self):
        u = self.u

        expected = list(range(4))
        u.dataIn._ag.data.extend(expected)

        self.runSim(9 * self.CLK)

        self.assertValSequenceEqual(u.dataOut._ag.data, expected)

    def test_multiple(self, sizeValues=[
            0, 1, 2, 3, 4, 4, 4, 4, 4,
            3, 3, 3, 3, 3, 3, 3, 3, 3,
            3, 3, 3, 3, 2, 1, 0]):
        u = self.u

        def openOutputAfterWile():
            u.dataOut._ag.setEnable(False)
            yield Timer(self.CLK * 9)
            u.dataOut._ag.setEnable(True)

        self.procs.append(openOutputAfterWile())

        expected = list(range(2 * 8))
        u.dataIn._ag.data.extend(expected)

        self.runSim(26 * self.CLK)

        collected = u.dataOut._ag.data
        if u.EXPORT_SIZE:
            self.assertValSequenceEqual(
                u.size._ag.data, sizeValues)

        self.assertValSequenceEqual(collected, expected)

    def test_tryMore(self):
        u = self.u

        ref = [i + 1 for i in range(self.ITEMS * 3)]
        u.dataIn._ag.data.extend(ref)

        def init():
            yield WaitWriteOnly()
            u.dataOut._ag.setEnable(False)

        self.procs.append(init())

        self.runSim(self.ITEMS * 4 * self.CLK)

        collected = u.dataOut._ag.data
        self.assertSetEqual(self.getFifoItems(), set(ref[:self.ITEMS]))
        self.assertValSequenceEqual(collected, [])
        self.assertValSequenceEqual(self.getUnconsumedInput(), ref[self.ITEMS:])

    def test_tryMore2(self, capturedOffset=2):
        u = self.u

        ref = [i + 1 for i in range(self.ITEMS * 2)]
        u.dataIn._ag.data.extend(ref)

        def closeOutput():
            yield Timer(self.OUT_CLK * 4)
            u.dataOut._ag.setEnable(False)

        self.procs.append(closeOutput())
        self.runSim(15 * self.CLK)

        collected = [int(x) for x in u.dataOut._ag.data]

        self.assertSetEqual(self.getFifoItems(),
                            set(ref[capturedOffset:self.ITEMS + capturedOffset]))
        se = self.assertSequenceEqual
        se(collected, ref[:capturedOffset])
        se(self.getUnconsumedInput(), ref[self.ITEMS + capturedOffset:])

    def test_randomizedIn(self):
        self._test_randomized(True, False)

    def test_randomizedOut(self):
        self._test_randomized(False, True)

    def test_randomizedAll(self):
        self._test_randomized(True, True)

    def _test_randomized(self, randIn, randOut):
        u = self.u
        LEN = 80
        ref = [i + 1 for i in range(LEN)]
        u.dataIn._ag.data.extend(ref)
        if randIn:
            self.randomize(u.dataIn)
        if randOut:
            self.randomize(u.dataOut)

        self.runSim(2.5 * LEN * self.CLK)

        collected = u.dataOut._ag.data
        self.assertSequenceEqual(collected, ref)

    def test_doloop(self):
        u = self.u
        u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])

        self.runSim(12 * self.CLK)

        collected = u.dataOut._ag.data
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], collected)
        self.assertSequenceEqual([], u.dataIn._ag.data)

    def test_nop(self):
        u = self.u
        self.runSim(12 * self.CLK)
        self.assertEqual(len(u.dataOut._ag.data), 0)

    def test_stuckedData(self):
        u = self.u
        u.dataIn._ag.data.append(1)

        def init():
            yield WaitWriteOnly()
            u.dataOut._ag.setEnable(False)

        self.procs.append(init())

        self.runSim(12 * self.CLK)
        self.assertEqual(len(u.dataOut._ag.data), 0)

    def test_withPause(self):
        u = self.u
        ref = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        u.dataIn._ag.data.extend(ref)

        def pause():
            yield Timer(3 * self.OUT_CLK)
            u.dataOut._ag.setEnable_asMonitor(False)

            yield Timer(3 * self.OUT_CLK)
            u.dataOut._ag.setEnable_asMonitor(True)

            yield Timer(3 * self.IN_CLK)
            u.dataIn._ag.setEnable_asDriver(False)

            yield Timer(3 * self.IN_CLK)
            u.dataIn._ag.setEnable_asDriver(True)

        self.procs.append(pause())

        self.runSim(20 * self.CLK)

        self.assertValSequenceEqual(u.dataOut._ag.data, ref)
        self.assertSequenceEqual(self.getUnconsumedInput(), [])

    def test_withPause2(self):
        u = self.u
        ref = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        u.dataIn._ag.data.extend(ref)

        def pause():
            yield Timer(4 * self.OUT_CLK)
            u.dataOut._ag.setEnable_asMonitor(False)
            yield Timer(3 * self.OUT_CLK)
            u.dataOut._ag.setEnable_asMonitor(True)
            yield Timer(3 * self.IN_CLK)
            u.dataIn._ag.setEnable_asDriver(False)
            yield Timer(3 * self.IN_CLK)
            u.dataIn._ag.setEnable_asDriver(True)

        self.procs.append(pause())

        self.runSim(20 * self.CLK)

        self.assertValSequenceEqual(u.dataOut._ag.data, ref)
        self.assertSequenceEqual(self.getUnconsumedInput(), [])

    def test_passdata(self):
        u = self.u
        ref = [1, 2, 3, 4, 5, 6]
        u.dataIn._ag.data.extend(ref)

        self.runSim(12 * self.CLK)

        self.assertValSequenceEqual(u.dataOut._ag.data, ref)
        self.assertValSequenceEqual(self.getUnconsumedInput(), [])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FifoWriterAgentTC))
    suite.addTest(unittest.makeSuite(FifoReaderAgentTC))
    suite.addTest(unittest.makeSuite(FifoTC))
    # suite.addTest(FifoTC("test_tryMore2"))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
