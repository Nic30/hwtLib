#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.abstract.denseMemory import DenseMemory
from hwtLib.structManipulators.cLinkedListWriter import CLinkedListWriter
from pycocotb.constants import CLK_PERIOD


class CLinkedListWriterTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = CLinkedListWriter()

        u.TIMEOUT = cls.TIMEOUT = 40
        u.ITEMS_IN_BLOCK = cls.ITEMS_IN_BLOCK = 31
        u.PTR_WIDTH = cls.PTR_WIDTH = 8
        u.BUFFER_CAPACITY = cls.BUFFER_CAPACITY = 7
        cls.MAX_LEN = cls.BUFFER_CAPACITY // 2 - 1
        return u

    def setUp(self):
        super(CLinkedListWriterTC, self).setUp()
        self.ID = int(self.u.ID)
        self.DATA_WIDTH = int(self.u.DATA_WIDTH)

    def test_nop(self):
        u = self.u
        for i in range(self.MAX_LEN + 1):
            self.u.dataIn._ag.data.append(i)

        self.runSim((self.TIMEOUT + 10) * CLK_PERIOD)

        self.assertEqual(len(u.rDatapump.req._ag.data), 0)
        self.assertEqual(len(u.wDatapump.req._ag.data), 0)
        self.assertEqual(len(u.wDatapump.w._ag.data), 0)

    def test_singleBurstReqNoData(self):
        u = self.u
        t = 20

        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.MAX_LEN + 1)

        self.runSim(t * CLK_PERIOD)

        req = u.wDatapump.req._ag.data
        self.assertEqual(len(req), 0)
        self.assertEqual(len(u.wDatapump.w._ag.data), 0)

    def test_singleBurst(self):
        u = self.u
        t = 20

        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.MAX_LEN + 1)

        for i in range(self.MAX_LEN + 1):
            self.u.dataIn._ag.data.append(i)

        self.runSim(t * CLK_PERIOD)

        self.assertValSequenceEqual(u.wDatapump.req._ag.data,
                                    [(self.ID, 0x1020, self.MAX_LEN, 0)])

        self.assertEqual(len(u.wDatapump.w._ag.data), self.MAX_LEN + 1)

    def test_waitForAck(self):
        u = self.u
        t = 20

        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.MAX_LEN + 1)

        for i in range(2 * (self.MAX_LEN + 1)):
            self.u.dataIn._ag.data.append(i)

        self.runSim(t * CLK_PERIOD)

        self.assertValSequenceEqual(u.wDatapump.req._ag.data,
                                    [(self.ID, 0x1020, self.MAX_LEN, 0)])

        self.assertEqual(len(u.wDatapump.w._ag.data), self.MAX_LEN + 1)

    def test_constrainedByPtrs(self):
        u = self.u
        t = 20

        u.baseAddr._ag.dout.append(0x1020)
        u.rdPtr._ag.dout.append(self.MAX_LEN)

        for i in range(self.MAX_LEN + 1):
            self.u.dataIn._ag.data.append(i)

        self.runSim(t * CLK_PERIOD)

        self.assertValSequenceEqual(u.wDatapump.req._ag.data,
                                    [(self.ID, 0x1020, self.MAX_LEN - 1, 0)])

        self.assertEqual(len(u.wDatapump.w._ag.data), self.MAX_LEN)

    def spotNextBaseAddr(self, mem, currentBase, nextBaseAddr):
        baseIndex = currentBase // (self.DATA_WIDTH // 8)
        mem.data[baseIndex + self.ITEMS_IN_BLOCK] = nextBaseAddr

    def test_regularUpload(self):
        u = self.u
        t = 100
        BASE = 0x1020
        ITEMS = 2 * (self.MAX_LEN + 1)
        MAGIC = 50

        u.baseAddr._ag.dout.append(BASE)
        u.rdPtr._ag.dout.append(ITEMS)

        m = DenseMemory(self.DATA_WIDTH, u.clk, u.rDatapump, u.wDatapump)

        self.spotNextBaseAddr(m, BASE, 0x2020)

        for i in range(ITEMS):
            self.u.dataIn._ag.data.append(i + MAGIC)

        self.runSim(t * CLK_PERIOD)

        baseIndex = BASE // (self.DATA_WIDTH // 8)
        # print()
        # self.debugNode(m, BASE)
        for i in range(ITEMS):
            try:
                d = m.data[baseIndex + i]
            except KeyError: # pragma: no cover
                raise AssertionError("Invalid data on index %d" % i)
            self.assertValEqual(d, i + MAGIC, "Invalid data on index %d" % i)

    def debugNode(self, mem, baseAddr): # pragma: no cover
        baseIndex = baseAddr // (self.DATA_WIDTH // 8)

        items = []
        for i in range(self.ITEMS_IN_BLOCK):
            try:
                d = mem.data[baseIndex + i]
            except KeyError:
                d = None
            items.append(d)
        try:
            nextAddr = mem.data[baseIndex + self.ITEMS_IN_BLOCK]
        except KeyError:
            nextAddr = None

        print("<Node 0x%x, items:%r\n    next:0x%x>" % (baseAddr, items, nextAddr))

    def test_regularUpload2(self):
        u = self.u
        t = 200
        BASE = 0x1020
        BASE2 = 0x2020
        ITEMS = self.ITEMS_IN_BLOCK * 2
        MAGIC = 50

        u.baseAddr._ag.dout.append(BASE)
        u.rdPtr._ag.dout.append(ITEMS)

        m = DenseMemory(self.DATA_WIDTH, u.clk, u.rDatapump, u.wDatapump)

        self.spotNextBaseAddr(m, BASE, BASE2)
        self.spotNextBaseAddr(m, BASE2, BASE + BASE2)
        self.spotNextBaseAddr(m, BASE + BASE2, BASE + BASE2 + BASE)

        for i in range(ITEMS):
            self.u.dataIn._ag.data.append(i + MAGIC)

        self.runSim(t * CLK_PERIOD)

        baseIndex = BASE // (self.DATA_WIDTH // 8)

        for i in range(ITEMS):
            try:
                d = m.data[baseIndex + i]
            except KeyError: # pragma: no cover
                raise AssertionError("Invalid data on index %d" % i)
            self.assertValEqual(d, i + MAGIC, "Invalid data on index %d" % i)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(CLinkedListWriterTC('test_regularUpload'))
    suite.addTest(unittest.makeSuite(CLinkedListWriterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
