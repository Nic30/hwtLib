#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hwIOs.std import HwIOFifoReader, HwIOFifoWriter
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.fifo import Fifo
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer, WaitWriteOnly


class FifoReaderPassTrought(HwModule):

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.din = HwIOFifoReader()
        self.dout = HwIOFifoReader()._m()

    @override
    def hwImpl(self):
        self.dout(self.din)


class FifoWriterPassTrought(FifoReaderPassTrought):

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.din = HwIOFifoWriter()
        self.dout = HwIOFifoWriter()._m()


class FifoReaderAgentTC(SimTestCase):
    CLK = CLK_PERIOD

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = FifoReaderPassTrought()
        cls.compileSim(cls.dut)

    def test_fifoReader(self):
        dut = self.dut
        self.randomize(dut.din)
        self.randomize(dut.dout)

        ref = [i for i in range(30)]
        dut.din._ag.data.extend(ref)
        self.runSim(120 * self.CLK)

        self.assertValSequenceEqual(dut.dout._ag.data, ref)


class FifoWriterAgentTC(SimTestCase):
    CLK = CLK_PERIOD

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = FifoWriterPassTrought()
        cls.compileSim(cls.dut)

    def test_fifoWriter(self):
        dut = self.dut

        self.randomize(dut.din)
        self.randomize(dut.dout)

        ref = [i for i in range(30)]
        dut.din._ag.data.extend(ref)
        self.runSim(120 * self.CLK)

        self.assertValSequenceEqual(dut.dout._ag.data, ref)


class FifoTC(SimTestCase):
    ITEMS = 4
    IN_CLK = CLK_PERIOD
    OUT_CLK = CLK_PERIOD
    CLK = max(IN_CLK, OUT_CLK)  # clock used for resolving of sim duration

    @classmethod
    @override
    def setUpClass(cls):
        dut = cls.dut = Fifo()
        dut.DATA_WIDTH = 8
        dut.DEPTH = cls.ITEMS
        dut.EXPORT_SIZE = True
        cls.compileSim(cls.dut)

    def getFifoItems(self):
        m = self.rtl_simulator.io.memory
        return set([int(x.read()) for x in m])

    def getUnconsumedInput(self):
        return self.dut.dataIn._ag.data

    def test_fifoSingleWord(self):
        dut = self.dut

        expected = [1]
        dut.dataIn._ag.data.extend(expected)

        self.runSim(9 * self.CLK)

        collected = dut.dataOut._ag.data
        self.assertValSequenceEqual(collected, expected)

    def test_fifoWriterDisable(self):
        dut = self.dut

        ref = [i + 1 for i in range(self.ITEMS)]
        dut.dataIn._ag.data.extend(ref)

        def init():
            dut.dataIn._ag.setEnable(False)
            return
            yield

        self.procs.append(init())

        self.runSim(8 * self.CLK)

        self.assertValSequenceEqual(dut.dataOut._ag.data, [])
        self.assertValSequenceEqual(self.getUnconsumedInput(), ref)

    def test_normalOp(self):
        dut = self.dut

        expected = list(range(4))
        dut.dataIn._ag.data.extend(expected)

        self.runSim(9 * self.CLK)

        self.assertValSequenceEqual(dut.dataOut._ag.data, expected)

    def test_multiple(self, sizeValues=[
            0, 1, 2, 3, 4, 4, 4, 4, 4,
            3, 3, 3, 3, 3, 3, 3, 3, 3,
            3, 3, 3, 3, 2, 1, 0, 0]):
        dut = self.dut

        def openOutputAfterWile():
            dut.dataOut._ag.setEnable(False)
            yield Timer(self.CLK * 9)
            dut.dataOut._ag.setEnable(True)

        self.procs.append(openOutputAfterWile())

        expected = list(range(2 * 8))
        dut.dataIn._ag.data.extend(expected)

        self.runSim(27 * self.CLK)

        collected = dut.dataOut._ag.data
        if dut.EXPORT_SIZE:
            self.assertValSequenceEqual(
                dut.size._ag.data, sizeValues)

        self.assertValSequenceEqual(collected, expected)

    def test_tryMore(self):
        dut = self.dut

        ref = [i + 1 for i in range(self.ITEMS * 3)]
        dut.dataIn._ag.data.extend(ref)

        def init():
            yield WaitWriteOnly()
            dut.dataOut._ag.setEnable(False)

        self.procs.append(init())

        self.runSim(self.ITEMS * 4 * self.CLK)

        collected = dut.dataOut._ag.data
        self.assertSetEqual(self.getFifoItems(), set(ref[:self.ITEMS]))
        self.assertValSequenceEqual(collected, [])
        self.assertValSequenceEqual(self.getUnconsumedInput(), ref[self.ITEMS:])

    def test_tryMore2(self, capturedOffset=2):
        dut = self.dut

        ref = [i + 1 for i in range(self.ITEMS * 2)]
        dut.dataIn._ag.data.extend(ref)

        def closeOutput():
            yield Timer(self.OUT_CLK * 4)
            dut.dataOut._ag.setEnable(False)

        self.procs.append(closeOutput())
        self.runSim(15 * self.CLK)

        collected = [int(x) for x in dut.dataOut._ag.data]

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
        dut = self.dut
        LEN = 80
        ref = [i + 1 for i in range(LEN)]
        dut.dataIn._ag.data.extend(ref)
        if randIn:
            self.randomize(dut.dataIn)
        if randOut:
            self.randomize(dut.dataOut)

        self.runSim(int(2.5 * LEN * self.CLK))

        collected = dut.dataOut._ag.data
        self.assertSequenceEqual(collected, ref)

    def test_doloop(self):
        dut = self.dut
        dut.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])

        self.runSim(12 * self.CLK)

        collected = dut.dataOut._ag.data
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], collected)
        self.assertSequenceEqual([], dut.dataIn._ag.data)

    def test_nop(self):
        dut = self.dut
        self.runSim(12 * self.CLK)
        self.assertEqual(len(dut.dataOut._ag.data), 0)

    def test_stuckedData(self):
        dut = self.dut
        dut.dataIn._ag.data.append(1)

        def init():
            yield WaitWriteOnly()
            dut.dataOut._ag.setEnable(False)

        self.procs.append(init())

        self.runSim(12 * self.CLK)
        self.assertEqual(len(dut.dataOut._ag.data), 0)

    def test_withPause(self):
        dut = self.dut
        ref = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        dut.dataIn._ag.data.extend(ref)

        def pause():
            yield Timer(3 * self.OUT_CLK)
            dut.dataOut._ag.setEnable_asMonitor(False)

            yield Timer(3 * self.OUT_CLK)
            dut.dataOut._ag.setEnable_asMonitor(True)

            yield Timer(3 * self.IN_CLK)
            dut.dataIn._ag.setEnable_asDriver(False)

            yield Timer(3 * self.IN_CLK)
            dut.dataIn._ag.setEnable_asDriver(True)

        self.procs.append(pause())

        self.runSim(20 * self.CLK)

        self.assertValSequenceEqual(dut.dataOut._ag.data, ref)
        self.assertSequenceEqual(self.getUnconsumedInput(), [])

    def test_withPause2(self):
        dut = self.dut
        ref = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        dut.dataIn._ag.data.extend(ref)

        def pause():
            yield Timer(4 * self.OUT_CLK)
            dut.dataOut._ag.setEnable_asMonitor(False)
            yield Timer(3 * self.OUT_CLK)
            dut.dataOut._ag.setEnable_asMonitor(True)
            yield Timer(3 * self.IN_CLK)
            dut.dataIn._ag.setEnable_asDriver(False)
            yield Timer(3 * self.IN_CLK)
            dut.dataIn._ag.setEnable_asDriver(True)

        self.procs.append(pause())

        self.runSim(20 * self.CLK)

        self.assertValSequenceEqual(dut.dataOut._ag.data, ref)
        self.assertSequenceEqual(self.getUnconsumedInput(), [])

    def test_passdata(self):
        dut = self.dut
        ref = [1, 2, 3, 4, 5, 6]
        dut.dataIn._ag.data.extend(ref)

        self.runSim(12 * self.CLK)

        self.assertValSequenceEqual(dut.dataOut._ag.data, ref)
        self.assertValSequenceEqual(self.getUnconsumedInput(), [])


if __name__ == "__main__":
    _ALL_TCs = [FifoWriterAgentTC, FifoReaderAgentTC, FifoTC]
    testLoader = unittest.TestLoader()
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
