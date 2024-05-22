#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.datapump.sim_ram import AxiDpSimRam
from hwtLib.structManipulators.cLinkedListWriter import CLinkedListWriter
from hwtSimApi.constants import CLK_PERIOD


class CLinkedListWriterTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = CLinkedListWriter()

        dut.TIMEOUT = cls.TIMEOUT = 40
        dut.ITEMS_IN_BLOCK = cls.ITEMS_IN_BLOCK = 31
        dut.PTR_WIDTH = cls.PTR_WIDTH = 8
        dut.BUFFER_CAPACITY = cls.BUFFER_CAPACITY = 7
        cls.MAX_LEN = cls.BUFFER_CAPACITY // 2 - 1
        cls.compileSim(dut)

    def setUp(self):
        super(CLinkedListWriterTC, self).setUp()
        self.ID = int(self.dut.ID)
        self.DATA_WIDTH = int(self.dut.DATA_WIDTH)

    def test_nop(self):
        dut = self.dut
        for i in range(self.MAX_LEN + 1):
            self.dut.dataIn._ag.data.append(i)

        self.runSim((self.TIMEOUT + 10) * CLK_PERIOD)

        self.assertEqual(len(dut.rDatapump.req._ag.data), 0)
        self.assertEqual(len(dut.wDatapump.req._ag.data), 0)
        self.assertEqual(len(dut.wDatapump.w._ag.data), 0)

    def test_singleBurstReqNoData(self):
        dut = self.dut
        t = 20

        dut.baseAddr._ag.dout.append(0x1020)
        dut.rdPtr._ag.dout.append(self.MAX_LEN + 1)

        self.runSim(t * CLK_PERIOD)

        req = dut.wDatapump.req._ag.data
        self.assertEqual(len(req), 0)
        self.assertEqual(len(dut.wDatapump.w._ag.data), 0)

    def test_singleBurst(self):
        dut = self.dut
        t = 20

        dut.baseAddr._ag.dout.append(0x1020)
        dut.rdPtr._ag.dout.append(self.MAX_LEN + 1)

        for i in range(self.MAX_LEN + 1):
            self.dut.dataIn._ag.data.append(i)

        self.runSim(t * CLK_PERIOD)

        self.assertValSequenceEqual(dut.wDatapump.req._ag.data,
                                    [(self.ID, 0x1020, self.MAX_LEN, 0)])

        self.assertEqual(len(dut.wDatapump.w._ag.data), self.MAX_LEN + 1)

    def test_waitForAck(self):
        dut = self.dut
        t = 20

        dut.baseAddr._ag.dout.append(0x1020)
        dut.rdPtr._ag.dout.append(self.MAX_LEN + 1)

        for i in range(2 * (self.MAX_LEN + 1)):
            self.dut.dataIn._ag.data.append(i)

        self.runSim(t * CLK_PERIOD)

        self.assertValSequenceEqual(dut.wDatapump.req._ag.data,
                                    [(self.ID, 0x1020, self.MAX_LEN, 0)])

        self.assertEqual(len(dut.wDatapump.w._ag.data), self.MAX_LEN + 1)

    def test_constrainedByPtrs(self):
        dut = self.dut
        t = 20

        dut.baseAddr._ag.dout.append(0x1020)
        dut.rdPtr._ag.dout.append(self.MAX_LEN)

        for i in range(self.MAX_LEN + 1):
            self.dut.dataIn._ag.data.append(i)

        self.runSim(t * CLK_PERIOD)

        self.assertValSequenceEqual(dut.wDatapump.req._ag.data,
                                    [(self.ID, 0x1020, self.MAX_LEN - 1, 0)])

        self.assertEqual(len(dut.wDatapump.w._ag.data), self.MAX_LEN)

    def spotNextBaseAddr(self, mem, currentBase, nextBaseAddr):
        baseIndex = currentBase // (self.DATA_WIDTH // 8)
        mem.data[baseIndex + self.ITEMS_IN_BLOCK] = nextBaseAddr

    def test_regularUpload(self):
        dut = self.dut
        t = 100
        BASE = 0x1020
        ITEMS = 2 * (self.MAX_LEN + 1)
        MAGIC = 50

        dut.baseAddr._ag.dout.append(BASE)
        dut.rdPtr._ag.dout.append(ITEMS)

        m = AxiDpSimRam(self.DATA_WIDTH, dut.clk, dut.rDatapump, dut.wDatapump)

        self.spotNextBaseAddr(m, BASE, 0x2020)

        for i in range(ITEMS):
            self.dut.dataIn._ag.data.append(i + MAGIC)

        self.runSim(t * CLK_PERIOD)

        baseIndex = BASE // (self.DATA_WIDTH // 8)
        # print()
        # self.debugNode(m, BASE)
        for i in range(ITEMS):
            try:
                d = m.data[baseIndex + i]
            except KeyError: # pragma: no cover
                raise AssertionError(f"Invalid data on index {i:d}")
            self.assertValEqual(d, i + MAGIC, f"Invalid data on index {i:d}")

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

        print(f"<Node 0x{baseAddr:x}, items:{items}\n    next:0x{nextAddr:x}>")

    def test_regularUpload2(self):
        dut = self.dut
        t = 200
        BASE = 0x1020
        BASE2 = 0x2020
        ITEMS = self.ITEMS_IN_BLOCK * 2
        MAGIC = 50

        dut.baseAddr._ag.dout.append(BASE)
        dut.rdPtr._ag.dout.append(ITEMS)

        m = AxiDpSimRam(self.DATA_WIDTH, dut.clk, dut.rDatapump, dut.wDatapump)

        self.spotNextBaseAddr(m, BASE, BASE2)
        self.spotNextBaseAddr(m, BASE2, BASE + BASE2)
        self.spotNextBaseAddr(m, BASE + BASE2, BASE + BASE2 + BASE)

        for i in range(ITEMS):
            self.dut.dataIn._ag.data.append(i + MAGIC)

        self.runSim(t * CLK_PERIOD)

        baseIndex = BASE // (self.DATA_WIDTH // 8)

        for i in range(ITEMS):
            try:
                d = m.data[baseIndex + i]
            except KeyError: # pragma: no cover
                raise AssertionError(f"Invalid data on index {i:d}")
            self.assertValEqual(d, i + MAGIC, f"Invalid data on index {i:d}")


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([CLinkedListWriterTC("test_regularUpload")])
    suite = testLoader.loadTestsFromTestCase(CLinkedListWriterTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
