#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import Time, NOP
from hwt.simulator.simTestCase import SimTestCase, \
    simpleRandomizationProcess
from hwtLib.amba.datapump.sim_ram import AxiDpSimRam
from hwtLib.structManipulators.arrayBuff_writer import ArrayBuff_writer
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer


class ArrayBuff_writer_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = ArrayBuff_writer()
        dut.TIMEOUT = 32
        cls.ID = int(dut.ID)
        cls.ITEMS = int(dut.ITEMS)
        cls.DATA_WIDTH = int(dut.DATA_WIDTH)
        cls.compileSim(dut)

    def test_nop(self):
        dut = self.dut
        self.runSim(10 * CLK_PERIOD)
        self.assertEqual(len(dut.wDatapump.req._ag.data), 0)
        self.assertEqual(len(dut.wDatapump.w._ag.data), 0)

        self.assertValEqual(self.dut.uploaded._ag.data[-1], 0)

    def test_timeout(self):
        dut = self.dut
        dut.items._ag.data.append(16)
        dut.baseAddr._ag.dout.append(0x1230)

        self.runSim(40 * CLK_PERIOD)

        req = dut.wDatapump.req._ag.data
        self.assertEmpty(dut.items._ag.data)
        self.assertValSequenceEqual(req, [
                                          (3, 0x1230, 0, 0)
                                         ])

        w = dut.wDatapump.w._ag.data
        self.assertValSequenceEqual(w, [
                                        (16, 255, 1)
                                       ])
        self.assertValEqual(self.dut.uploaded._ag.data[-1], 0)

    def test_multipleTimeout(self):
        dut = self.dut
        N = 2

        dut.baseAddr._ag.dout.append(0x1230)

        def itemsWithDelay():
            addSize = dut.items._ag.data.append
            addSize(16)
            yield Timer(40 * CLK_PERIOD)
            dut.wDatapump.ack._ag.data.append(self.ID)
            addSize(17)
            dut.wDatapump.ack._ag.data.append(self.ID)

        self.procs.append(itemsWithDelay())

        self.runSim(80 * CLK_PERIOD)

        self.assertEmpty(dut.items._ag.data)

        self.assertValSequenceEqual(dut.wDatapump.req._ag.data,
                                    [
                                     (3, 0x1230 + i * 8, 0, 0) for i in range(N)
                                    ])

        self.assertValSequenceEqual(dut.wDatapump.w._ag.data,
                                    [
                                     (16 + i, 255, 1) for i in range(N)
                                    ])

        self.assertValEqual(self.rtl_simulator.model.io.uploadedCntr, 2)

    def test_timeoutWithMore(self):
        dut = self.dut

        dut.items._ag.data.extend([16, 28, 99])
        dut.baseAddr._ag.dout.append(0x1230)

        dut.wDatapump.ack._ag.data.extend([NOP for _ in range(32 + 3 * 2)])
        dut.wDatapump.ack._ag.data.append(self.ID)

        self.runSim(70 * CLK_PERIOD)
        self.assertEqual(len(dut.items._ag.data), 0)
        req = dut.wDatapump.req._ag.data
        self.assertValSequenceEqual(req,
                                    [
                                       (self.ID, 0x1230, 2, 0)
                                    ])

        w = dut.wDatapump.w._ag.data
        self.assertValSequenceEqual(w,
                                    [(16, 255, 0),
                                     (28, 255, 0),
                                     (99, 255, 1)])

        self.assertEqual(len(dut.wDatapump.ack._ag.data), 0)

        self.assertValEqual(self.dut.uploaded._ag.data[-1], 3)

    def test_fullFill(self):
        dut = self.dut
        N = 16

        dut.baseAddr._ag.dout.append(0x1230)
        dut.items._ag.data.extend([88 for _ in range(N)])
        dut.wDatapump.ack._ag.data.extend([NOP for _ in range(N * 2)] + [self.ID, ])

        self.runSim(40 * CLK_PERIOD)

        self.assertEqual(len(dut.items._ag.data), 0)

        self.assertValSequenceEqual(dut.wDatapump.req._ag.data,
                                    [
                                     (self.ID, 0x1230, N - 1, 0)
                                     ])
        self.assertValSequenceEqual(dut.wDatapump.w._ag.data,
                                    [
                                     (88, 255, int(i == 15)) for i in range(N)
                                     ])

        self.assertEmpty(dut.wDatapump.ack._ag.data)

        self.assertValEqual(self.dut.uploaded._ag.data[-1], N)

    def test_fullFill_randomized(self):
        dut = self.dut
        N = 2 * 16 - 1
        m = AxiDpSimRam(self.DATA_WIDTH, dut.clk, wDatapumpHwIO=dut.wDatapump)
        ITEM_SIZE = self.DATA_WIDTH // 8
        MAGIC = 88

        self.randomize(dut.items)
        self.randomize(dut.wDatapump.w)
        self.randomize(dut.wDatapump.req)
        self.randomize(dut.wDatapump.ack)

        BASE = m.malloc(ITEM_SIZE * N)
        dut.baseAddr._ag.dout.append(BASE)
        dut.items._ag.data.extend([MAGIC + i for i in range(N)])

        self.runSim(200 * CLK_PERIOD)

        self.assertEmpty(dut.items._ag.data)

        self.assertEmpty(dut.wDatapump.ack._ag.data)

        BASE_INDX = BASE // ITEM_SIZE
        for i in range(N):
            self.assertEqual(m.data[BASE_INDX + i], MAGIC + i)

        self.assertValEqual(self.dut.uploaded._ag.data[-1], N)

    def test_fullFill_extraAck(self):
        dut = self.dut
        N = 16
        # randomize = self.randomize

        dut.baseAddr._ag.dout.append(0x1230)
        dut.items._ag.data.extend([1 + i for i in range(N)])
        dut.wDatapump.ack._ag.data.extend([NOP for _ in range(N * 2 - 1)] +
                                        [self.ID + 1, self.ID, self.ID + 1])

        # randomize(dut.wDatapump.w)
        # randomize(dut.items)
        # randomize(dut.wDatapump.req)
        # randomize(dut.wDatapump.ack)

        self.runSim(150 * CLK_PERIOD)

        self.assertEqual(len(dut.items._ag.data), 0)

        self.assertValSequenceEqual(dut.wDatapump.req._ag.data,
                                    [(self.ID, 0x1230, N - 1, 0)])
        w = dut.wDatapump.w._ag.data
        self.assertEqual(len(w), N)
        self.assertEqual(dut.wDatapump.ack._ag.actualData, self.ID + 1)

        self.assertValEqual(self.dut.uploaded._ag.data[-1], N)

    def test_fullFill_withoutAck(self):
        dut = self.dut
        N = 16

        dut.baseAddr._ag.dout.append(0x1230)
        dut.items._ag.data.extend([1 + i for i in range(N)])

        self.runSim(150 * CLK_PERIOD)

        self.assertEqual(len(dut.items._ag.data), 0)

        self.assertValSequenceEqual(dut.wDatapump.req._ag.data,
                                    [(self.ID, 0x1230, N - 1, 0)])
        w = dut.wDatapump.w._ag.data
        self.assertEqual(len(w), N)

        self.assertValEqual(self.dut.uploaded._ag.data[-1], 0)

    def test_fullFill_randomized3(self, N=None):
        dut = self.dut
        BASE = 0x1230
        MAGIC = 1
        if N is None:
            N = self.ITEMS + 10

        m = AxiDpSimRam(self.DATA_WIDTH, dut.clk, wDatapumpHwIO=dut.wDatapump)

        dut.baseAddr._ag.dout.append(BASE)
        for i in range(N):
            dut.items._ag.data.append(MAGIC + i)

        def enReq():
            dut.wDatapump.req._ag.enable = False
            yield Timer(32 * CLK_PERIOD)
            yield from simpleRandomizationProcess(self, dut.wDatapump.req._ag)()

        self.procs.append(enReq())

        self.randomize(dut.wDatapump.w)
        self.randomize(dut.items)
        # self.randomize(dut.req)
        self.randomize(dut.wDatapump.ack)

        self.runSim(N * 40 * Time.ns)

        self.assertEmpty(dut.items._ag.data)
        d = m.getArray(BASE, self.DATA_WIDTH // 8, self.ITEMS)

        expected = [i + MAGIC if i >= 10 else i + self.ITEMS + MAGIC
                    for i in range(self.ITEMS)]

        self.assertValSequenceEqual(d, expected)
        self.assertValEqual(dut.uploaded._ag.data[-1], N)

    # def test_fullFill_randomized4(self):
    #    self.test_fullFill_randomized3(N=3*self.ITEMS)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([ArrayBuff_writer_TC("test_fullFill_withoutAck")])
    suite = testLoader.loadTestsFromTestCase(ArrayBuff_writer_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
