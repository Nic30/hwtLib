#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time, NOP
from hwt.simulator.simTestCase import SingleUnitSimTestCase, \
    simpleRandomizationProcess
from hwtLib.abstract.denseMemory import DenseMemory
from hwtLib.structManipulators.arrayBuff_writer import ArrayBuff_writer
from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer


class ArrayBuff_writer_TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = u = ArrayBuff_writer()
        u.TIMEOUT = 32
        cls.ID = int(u.ID)
        cls.ITEMS = int(u.ITEMS)
        cls.DATA_WIDTH = int(u.DATA_WIDTH)
        return u

    def test_nop(self):
        u = self.u
        self.runSim(10 * CLK_PERIOD)
        self.assertEqual(len(u.wDatapump.req._ag.data), 0)
        self.assertEqual(len(u.wDatapump.w._ag.data), 0)

        self.assertValEqual(self.u.uploaded._ag.data[-1], 0)

    def test_timeout(self):
        u = self.u
        u.items._ag.data.append(16)
        u.baseAddr._ag.dout.append(0x1230)

        self.runSim(40 * CLK_PERIOD)

        req = u.wDatapump.req._ag.data
        self.assertEmpty(u.items._ag.data)
        self.assertValSequenceEqual(req, [
                                          (3, 0x1230, 0, 0)
                                         ])

        w = u.wDatapump.w._ag.data
        self.assertValSequenceEqual(w, [
                                        (16, 255, 1)
                                       ])
        self.assertValEqual(self.u.uploaded._ag.data[-1], 0)

    def test_multipleTimeout(self):
        u = self.u
        N = 2

        u.baseAddr._ag.dout.append(0x1230)

        def itemsWithDelay():
            addSize = u.items._ag.data.append
            addSize(16)
            yield Timer(40 * CLK_PERIOD)
            u.wDatapump.ack._ag.data.append(self.ID)
            addSize(17)
            u.wDatapump.ack._ag.data.append(self.ID)

        self.procs.append(itemsWithDelay())

        self.runSim(80 * CLK_PERIOD)

        self.assertEmpty(u.items._ag.data)

        self.assertValSequenceEqual(u.wDatapump.req._ag.data,
                                    [
                                     (3, 0x1230 + i * 8, 0, 0) for i in range(N)
                                    ])

        self.assertValSequenceEqual(u.wDatapump.w._ag.data,
                                    [
                                     (16 + i, 255, 1) for i in range(N)
                                    ])

        self.assertValEqual(self.rtl_simulator.model.io.uploadedCntr, 2)

    def test_timeoutWithMore(self):
        u = self.u

        u.items._ag.data.extend([16, 28, 99])
        u.baseAddr._ag.dout.append(0x1230)

        u.wDatapump.ack._ag.data.extend([NOP for _ in range(32 + 3 * 2)])
        u.wDatapump.ack._ag.data.append(self.ID)

        self.runSim(70 * CLK_PERIOD)
        self.assertEqual(len(u.items._ag.data), 0)
        req = u.wDatapump.req._ag.data
        self.assertValSequenceEqual(req,
                                    [
                                       (self.ID, 0x1230, 2, 0)
                                    ])

        w = u.wDatapump.w._ag.data
        self.assertValSequenceEqual(w,
                                    [(16, 255, 0),
                                     (28, 255, 0),
                                     (99, 255, 1)])

        self.assertEqual(len(u.wDatapump.ack._ag.data), 0)

        self.assertValEqual(self.u.uploaded._ag.data[-1], 3)

    def test_fullFill(self):
        u = self.u
        N = 16

        u.baseAddr._ag.dout.append(0x1230)
        u.items._ag.data.extend([88 for _ in range(N)])
        u.wDatapump.ack._ag.data.extend([NOP for _ in range(N * 2)] + [self.ID, ])

        self.runSim(40 * CLK_PERIOD)

        self.assertEqual(len(u.items._ag.data), 0)

        self.assertValSequenceEqual(u.wDatapump.req._ag.data,
                                    [
                                     (self.ID, 0x1230, N - 1, 0)
                                     ])
        self.assertValSequenceEqual(u.wDatapump.w._ag.data,
                                    [
                                     (88, 255, int(i == 15)) for i in range(N)
                                     ])

        self.assertEmpty(u.wDatapump.ack._ag.data)

        self.assertValEqual(self.u.uploaded._ag.data[-1], N)

    def test_fullFill_randomized(self):
        u = self.u
        N = 2 * 16 - 1
        m = DenseMemory(self.DATA_WIDTH, u.clk, wDatapumpIntf=u.wDatapump)
        ITEM_SIZE = self.DATA_WIDTH // 8
        MAGIC = 88

        self.randomize(u.items)
        self.randomize(u.wDatapump.w)
        self.randomize(u.wDatapump.req)
        self.randomize(u.wDatapump.ack)

        BASE = m.malloc(ITEM_SIZE * N)
        u.baseAddr._ag.dout.append(BASE)
        u.items._ag.data.extend([MAGIC + i for i in range(N)])

        self.runSim(200 * CLK_PERIOD)

        self.assertEmpty(u.items._ag.data)

        self.assertEmpty(u.wDatapump.ack._ag.data)

        BASE_INDX = BASE // ITEM_SIZE
        for i in range(N):
            self.assertEqual(m.data[BASE_INDX + i], MAGIC + i)

        self.assertValEqual(self.u.uploaded._ag.data[-1], N)

    def test_fullFill_extraAck(self):
        u = self.u
        N = 16
        # randomize = self.randomize

        u.baseAddr._ag.dout.append(0x1230)
        u.items._ag.data.extend([1 + i for i in range(N)])
        u.wDatapump.ack._ag.data.extend([NOP for _ in range(N * 2 - 1)] + 
                                        [self.ID + 1, self.ID, self.ID + 1])

        # randomize(u.wDatapump.w)
        # randomize(u.items)
        # randomize(u.wDatapump.req)
        # randomize(u.wDatapump.ack)

        self.runSim(150 * CLK_PERIOD)

        self.assertEqual(len(u.items._ag.data), 0)

        self.assertValSequenceEqual(u.wDatapump.req._ag.data,
                                    [(self.ID, 0x1230, N - 1, 0)])
        w = u.wDatapump.w._ag.data
        self.assertEqual(len(w), N)
        self.assertEqual(u.wDatapump.ack._ag.actualData, self.ID + 1)

        self.assertValEqual(self.u.uploaded._ag.data[-1], N)

    def test_fullFill_withoutAck(self):
        u = self.u
        N = 16

        u.baseAddr._ag.dout.append(0x1230)
        u.items._ag.data.extend([1 + i for i in range(N)])

        self.runSim(150 * CLK_PERIOD)

        self.assertEqual(len(u.items._ag.data), 0)

        self.assertValSequenceEqual(u.wDatapump.req._ag.data,
                                    [(self.ID, 0x1230, N - 1, 0)])
        w = u.wDatapump.w._ag.data
        self.assertEqual(len(w), N)

        self.assertValEqual(self.u.uploaded._ag.data[-1], 0)

    def test_fullFill_randomized3(self, N=None):
        u = self.u
        BASE = 0x1230
        MAGIC = 1
        if N is None:
            N = self.ITEMS + 10

        m = DenseMemory(self.DATA_WIDTH, u.clk, wDatapumpIntf=u.wDatapump)

        u.baseAddr._ag.dout.append(BASE)
        for i in range(N):
            u.items._ag.data.append(MAGIC + i)

        def enReq():
            u.wDatapump.req._ag.enable = False
            yield Timer(32 * CLK_PERIOD)
            yield from simpleRandomizationProcess(self, u.wDatapump.req._ag)()

        self.procs.append(enReq())

        self.randomize(u.wDatapump.w)
        self.randomize(u.items)
        # self.randomize(u.req)
        self.randomize(u.wDatapump.ack)

        self.runSim(N * 40 * Time.ns)

        self.assertEmpty(u.items._ag.data)
        d = m.getArray(BASE, self.DATA_WIDTH // 8, self.ITEMS)

        expected = [i + MAGIC if i >= 10 else i + self.ITEMS + MAGIC
                    for i in range(self.ITEMS)]

        self.assertValSequenceEqual(d, expected)
        self.assertValEqual(u.uploaded._ag.data[-1], N)

    # def test_fullFill_randomized4(self):
    #    self.test_fullFill_randomized3(N=3*self.ITEMS)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(ArrayBuff_writer_TC('test_fullFill_withoutAck'))
    suite.addTest(unittest.makeSuite(ArrayBuff_writer_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
