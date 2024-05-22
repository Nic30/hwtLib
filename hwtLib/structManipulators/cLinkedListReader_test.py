#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import NOP
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.datapump.sim_ram import AxiDpSimRam
from hwtLib.structManipulators.cLinkedListReader import CLinkedListReader
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class CLinkedListReaderTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = CLinkedListReader()
        cls.ITEMS_IN_BLOCK = 31
        cls.PTR_WIDTH = 8
        cls.BUFFER_CAPACITY = 8
        cls.DATA_WIDTH = 64

        cls.ID = int(cls.dut.ID)
        cls.ID_LAST = int(cls.dut.ID_LAST)
        cls.MAX_LEN = cls.BUFFER_CAPACITY // 2 - 1

        dut.ITEMS_IN_BLOCK = cls.ITEMS_IN_BLOCK
        dut.PTR_WIDTH = cls.PTR_WIDTH
        dut.BUFFER_CAPACITY = cls.BUFFER_CAPACITY
        dut.DATA_WIDTH = cls.DATA_WIDTH
        cls.compileSim(dut)

    def test_tailHeadPrincipe(self):
        BITS = 16
        MASK = mask(BITS)
        tail = 0
        head = 0

        def normalize(n):
            if n < 0:
                return MASK + n
            elif n > MASK:
                return n - MASK
            else:
                return n

        def size():
            return normalize(head - tail)

        self.assertEqual(size(), 0)

        head = MASK

        self.assertEqual(size(), MASK)

        tail = 10
        self.assertEqual(size(), MASK - 10)

        head = normalize(head + 5)
        self.assertEqual(size(), MASK - 5)

    def test_nop(self):
        dut = self.dut
        self.runSim(20 * CLK_PERIOD)

        self.assertEqual(len(dut.rDatapump.req._ag.data), 0)
        self.assertEqual(len(dut.dataOut._ag.data), 0)

    def test_singleDescrReq(self):
        dut = self.dut
        t = 20

        dut.baseAddr._ag.dout.append(0x1020)
        dut.wrPtr._ag.dout.append(self.MAX_LEN + 1)

        self.runSim(t * CLK_PERIOD)

        req = dut.rDatapump.req._ag.data
        self.assertEmpty(dut.dataOut._ag.data)

        self.assertValSequenceEqual(req,
                                    [(self.ID, 0x1020, self.MAX_LEN, 0),
                                     ])

    def test_singleDescrReqOnEdge(self):
        dut = self.dut
        t = 20

        dut.baseAddr._ag.dout.append(0x1020)
        dut.rdPtr._ag.dout.append(mask(self.PTR_WIDTH))
        dut.wrPtr._ag.dout.append(self.MAX_LEN)  # space is self.MAX_LEN + 1

        self.runSim(t * CLK_PERIOD)

        req = dut.rDatapump.req._ag.data
        self.assertEqual(len(dut.dataOut._ag.data), 0)

        self.assertValSequenceEqual(req,
                                    [(self.ID, 0x1020, self.MAX_LEN, 0)])

    def test_singleDescrReqOnEdge2(self):
        dut = self.dut
        t = 20

        dut.baseAddr._ag.dout.append(0x1020)
        dut.rdPtr._ag.dout.append(mask(self.PTR_WIDTH))
        dut.wrPtr._ag.dout.append(self.MAX_LEN - 1)  # space is self.MAX_LEN

        self.runSim(t * CLK_PERIOD)

        req = dut.rDatapump.req._ag.data
        self.assertEmpty(dut.dataOut._ag.data)

        self.assertValSequenceEqual(req,
                                    [(self.ID, 0x1020, self.MAX_LEN - 1, 0),
                                     ])

    def test_singleDescrReqMax(self):
        dut = self.dut
        t = 20
        N = self.MAX_LEN + 1

        dut.baseAddr._ag.dout.append(0x1020)
        dut.wrPtr._ag.dout.append(N * (self.MAX_LEN + 1))

        self.runSim(t * CLK_PERIOD)

        req = dut.rDatapump.req._ag.data
        self.assertEqual(len(dut.dataOut._ag.data), 0)

        self.assertValSequenceEqual(req,
                                    [
                                     (self.ID, 0x1020, self.MAX_LEN, 0)
                                     ])

    def test_singleDescrWithData(self):
        dut = self.dut
        t = 25
        N = self.MAX_LEN + 1
        ADDR_BASE = 0x1020
        dut.baseAddr._ag.dout.append(0x1020)
        dut.wrPtr._ag.dout.extend([NOP, N])

        expectedReq, reqData = self.generateRequests(ADDR_BASE, [N])
        dut.rDatapump.r._ag.data.extend(reqData)
        self.runSim(t * CLK_PERIOD)
        self.checkOutputs(expectedReq, N)

    def test_downloadFullBlock(self):
        dut = self.dut
        N = self.ITEMS_IN_BLOCK
        ADDR_BASE = 0x1020

        dut.baseAddr._ag.dout.append(ADDR_BASE)
        dut.wrPtr._ag.dout.extend([NOP, N])
        expectedReq, reqData = self.generateRequests(ADDR_BASE, [N])
        dut.rDatapump.r._ag.data.extend(reqData)

        self.runSim((len(reqData) + len(expectedReq) + 50) * CLK_PERIOD)
        self.checkOutputs(expectedReq, N)

    def test_downloadFullBlockRandomized(self):
        dut = self.dut
        N = self.ITEMS_IN_BLOCK
        MAGIC = 6413

        m = AxiDpSimRam(self.DATA_WIDTH, dut.clk, dut.rDatapump)

        ADDR_BASE, data = self.createBlock(m, MAGIC)
        self.updateNextAddr(m, ADDR_BASE, ADDR_BASE)

        self.randomize(dut.rDatapump.r)
        self.randomize(dut.rDatapump.req)
        self.randomize(dut.dataOut)

        dut.baseAddr._ag.dout.append(ADDR_BASE)
        dut.wrPtr._ag.dout.extend([NOP, N])

        self.runSim(N * 6 * CLK_PERIOD)
        self.assertValSequenceEqual(dut.dataOut._ag.data, data)

    def createBlock(self, mem, seed):
        data = [i + seed for i in range(self.ITEMS_IN_BLOCK)]
        addr = mem.calloc(self.ITEMS_IN_BLOCK + 1,
                          self.DATA_WIDTH // 8,
                          keepOut=0x1020,
                          initValues=data + [None])
        return addr, data

    def updateNextAddr(self, mem, addrOfBlock, addrOfNextBlock):
        mem.data[addrOfBlock // mem.cellSize + self.ITEMS_IN_BLOCK]\
            = addrOfNextBlock

    def test_downloadFullBlockRandomized5x(self):
        dut = self.dut
        N = self.ITEMS_IN_BLOCK * 5
        MAGIC = 456
        m = AxiDpSimRam(self.DATA_WIDTH, dut.clk, dut.rDatapump)

        data = []
        ADDR_BASE = None
        lastAddr = None
        for i in range(5):
            a, d = self.createBlock(m, i * MAGIC)
            if ADDR_BASE is None:
                ADDR_BASE = a
            if lastAddr is not None:
                self.updateNextAddr(m, lastAddr, a)
            lastAddr = a
            data.extend(d)
        self.updateNextAddr(m, lastAddr, ADDR_BASE)

        self.randomize(dut.rDatapump.r)
        self.randomize(dut.rDatapump.req)
        self.randomize(dut.dataOut)

        dut.baseAddr._ag.dout.append(ADDR_BASE)
        dut.wrPtr._ag.dout.extend([NOP, N])

        self.runSim(N * 5 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.dataOut._ag.data, data)

    def test_downloadFullBlockNextAddrInSeparateReq(self):
        dut = self.dut
        N = self.ITEMS_IN_BLOCK + 1
        MAGIC = 5896

        m = AxiDpSimRam(self.DATA_WIDTH, dut.clk, dut.rDatapump)

        ADDR_BASE, data = self.createBlock(m, MAGIC)
        NEXT_BASE, data2 = self.createBlock(m, MAGIC*2)
        self.updateNextAddr(m, ADDR_BASE, NEXT_BASE)

        dut.baseAddr._ag.dout.append(ADDR_BASE)
        dut.wrPtr._ag.dout.extend([NOP, self.MAX_LEN]
                                + [NOP for _ in range(self.MAX_LEN + 4)] + [N])

        self.runSim(N * 5 * CLK_PERIOD)
        self.assertValSequenceEqual(dut.dataOut._ag.data, data + [data2[0]])

    def checkOutputs(self, expectedReq, itemsCnt):
        req = self.dut.rDatapump.req._ag.data
        dout = self.dut.dataOut._ag.data

        self.assertValSequenceEqual(req, expectedReq)

        self.assertEqual(len(dout), itemsCnt)
        for i, d in enumerate(dout):
            self.assertValEqual(d, i)

    def generateRequests(self, baseAddress, spaceValues):
        """
        Generate reference requests and data
        data words are containing it's indexes,
        baseAddresses are multiplies baseAddress

        :param spaceValues: is iterable of space values
        """
        requests = []
        responses = []
        wordCntr = 0
        inBlockRem = self.ITEMS_IN_BLOCK
        _baseAddress = baseAddress
        for space in spaceValues:
            while space != 0:
                constraingSpace = min(inBlockRem, space)
                reqId = self.ID
                if constraingSpace > self.MAX_LEN + 1:
                    reqLen = self.MAX_LEN
                elif inBlockRem == 0:
                    reqLen = 0
                    reqId = self.ID_LAST
                else:
                    if (constraingSpace <= self.MAX_LEN + 1
                            and inBlockRem < self.MAX_LEN + 1):
                        # we will download next* as well
                        reqLen = constraingSpace
                        reqId = self.ID_LAST
                    else:
                        # if constraingSpace == inBlockRem:
                        #    reqId = self.ID_LAST
                        #    reqLen = constraingSpace
                        # else:
                        reqLen = constraingSpace - 1

                inBlockIndex = self.ITEMS_IN_BLOCK - inBlockRem
                req = (reqId, _baseAddress + inBlockIndex * 8, reqLen, 0)
                requests.append(req)

                for i in range(reqLen + 1):
                    if i == reqLen and reqId == self.ID_LAST:
                        r = (reqId, baseAddress, mask(8), True)
                        _baseAddress += baseAddress
                    else:
                        r = (reqId, wordCntr + i, mask(8), i == reqLen)

                    responses.append(r)

                if reqId == self.ID_LAST:
                    inBlockRem = self.ITEMS_IN_BLOCK
                    wordCntr += reqLen
                    space -= reqLen
                else:
                    inBlockRem -= reqLen + 1
                    wordCntr += reqLen + 1
                    space -= reqLen + 1

        return requests, responses


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([CLinkedListReaderTC("test_downloadFullBlockRandomized")])
    suite = testLoader.loadTestsFromTestCase(CLinkedListReaderTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
