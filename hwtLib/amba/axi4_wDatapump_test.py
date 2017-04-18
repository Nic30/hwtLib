#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi3 import Axi3_addr
from hwtLib.amba.axi4 import Axi4_addr
from hwtLib.amba.axi4_rDatapump_test import Axi4_rDatapumpTC
from hwtLib.amba.axi4_wDatapump import Axi_wDatapump
from hwtLib.amba.constants import RESP_OKAY, BYTES_IN_TRANS
from hwt.synthesizer.param import evalParam
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem


class Axi4_wDatapumpTC(SimTestCase):
    LEN_MAX = Axi4_rDatapumpTC.LEN_MAX

    def setUp(self):
        super(Axi4_wDatapumpTC, self).setUp()
        self.u = u = Axi_wDatapump(axiAddrCls=Axi4_addr)
        u.MAX_LEN.set(16)
        self.prepareUnit(u)

    def test_nop(self):
        u = self.u

        self.doSim(200 * Time.ns)

        self.assertEmpty(u.a._ag.data)
        self.assertEmpty(u.w._ag.data)

    def test_simple(self):
        u = self.u

        req = u.driver._ag.req
        aw = u.a._ag.data

        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, 0))

        self.doSim(200 * Time.ns)

        self.assertValSequenceEqual(aw,
                                    [
                                     (0, 255, 1, 3, 0, 0, 0, BYTES_IN_TRANS(8), 0)
                                    ])

        self.assertEmpty(u.w._ag.data)

    def test_simpleWithData(self):
        u = self.u

        req = u.driver._ag.req
        aw = u.a._ag.data
        wIn = u.driver.w._ag
        w = u.w._ag.data
        b = u.b._ag.data

        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, 0))
        wIn.data.append((77, mask(64 // 8 - 1), 1))
        b.append((0, RESP_OKAY))

        self.doSim(200 * Time.ns)

        self.assertValSequenceEqual(aw, [ 
                                         (0, 255, 1, 3, 0, 0, 0, BYTES_IN_TRANS(8), 0)
                                         ])

        self.assertEqual(len(w), 1)
        self.assertEmpty(b)

    def test_singleLong(self):
        u = self.u

        req = u.driver._ag.req
        aw = u.a._ag.data
        wIn = u.driver.w._ag
        w = u.w._ag.data
        b = u.b._ag.data

        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, self.LEN_MAX))
        for i in range(self.LEN_MAX + 1 + 10):
            wIn.data.append((100 + 1, mask(8), i == self.LEN_MAX))
        b.append((0, RESP_OKAY))

        self.doSim((10 + self.LEN_MAX) * 10 * Time.ns)

        self.assertValSequenceEqual(aw,
                                 [(0, 0xff, 1, 3, self.LEN_MAX, 0, 0, BYTES_IN_TRANS(8), 0)])

        self.assertEqual(len(w), self.LEN_MAX + 1)
        self.assertEmpty(b)
        self.assertEqual(len(u.driver._ag.ack.data), 1)

    def test_multiple(self):
        u = self.u
        req = u.driver._ag.req
        aw = u.a._ag.data
        wIn = u.driver.w._ag
        w = u.w._ag.data
        b = u.b._ag.data
        N = 50

        # download one word from addr 0xff
        for i in range(N):
            req.data.append(req.mkReq((i * 8) + 0xff, 0))
            wIn.data.append((77, mask(64 // 8 - 1), 1))
            b.append((0, RESP_OKAY))

        self.doSim(1000 * Time.ns)

        self.assertValSequenceEqual(aw,
                                   [
                                    (0, 0xff + (8 * i), 1, 3, 0, 0, 0, BYTES_IN_TRANS(8), 0)
                                     for i in range(N)
                                    ])

        self.assertEqual(len(w), N)
        self.assertEqual(len(b), 0)
        self.assertEqual(len(u.driver._ag.ack.data), N)

    def test_multiple_randomized(self):
        u = self.u
        req = u.driver._ag.req
        aw = u.a._ag.data
        wIn = u.driver.w._ag
        w = u.w._ag.data
        b = u.b._ag.data
        N = 50

        # download one word from addr 0xff
        for i in range(N):
            req.data.append(req.mkReq((i * 8) + 0xff, 0))
            wIn.data.append((77, mask(64 // 8 - 1), 1))
            b.append((0, RESP_OKAY))

        ra = self.randomize
        ra(u.a)
        ra(u.b)
        ra(u.driver.req)
        ra(u.driver.ack)
        ra(u.w)
        ra(u.driver.w)

        self.doSim(N * 6 * 10 * Time.ns)

        self.assertValSequenceEqual(aw,
                                    [
                                      (0, 0xff + (8 * i), 1, 3, 0, 0, 0, BYTES_IN_TRANS(8), 0)
                                      for i in range(N)
                                    ])

        self.assertEqual(len(w), N)
        self.assertEmpty(b)
        self.assertEqual(len(u.driver._ag.ack.data), N)

    def test_multiple_randomized2(self):
        u = self.u
        req = u.driver._ag.req
        aw = u.a._ag.data
        wIn = u.driver.w._ag
        w = u.w._ag.data
        b = u.b._ag.data
        N = 50
        L = 3
        expectedWData = []

        # download one word from addr 0xff
        for i in range(N):
            req.data.append(req.mkReq((i * 8) + 0xff, L - 1))
            for i in range(L):
                d = 77 + i
                m = mask(64 // 8 - 1)
                l = i == (L - 1)
                wIn.data.append((d, m, l))
                expectedWData.append((0, d, m, int(l)))
            b.append((0, RESP_OKAY))

        ra = self.randomize
        ra(u.a)
        ra(u.b)
        ra(u.driver.req)
        ra(u.driver.ack)
        ra(u.w)
        ra(u.driver.w)

        self.doSim(N * L * 10 * 5 * Time.ns)

        self.assertValSequenceEqual(aw,
                                    [
                                      (0, 0xff + (8 * i), 1, 3, L - 1, 0, 0, BYTES_IN_TRANS(8), 0)
                                      for i in range(N)
                                    ])

        self.assertEqual(len(w), N * 3)
        for expWD, wd in zip(expectedWData, w):
            self.assertValSequenceEqual(wd, expWD)

        self.assertEqual(len(b), 0)
        self.assertEqual(len(u.driver._ag.ack.data), N)


class Axi3_wDatapump_direct_TC(Axi4_wDatapumpTC):
    LEN_MAX = 16

    def setUp(self):
        u = Axi_wDatapump(axiAddrCls=Axi3_addr)
        u.MAX_LEN.set(16)
        self.prepareUnit(u)


class Axi3_wDatapump_small_splitting_TC(SimTestCase):
    LEN_MAX = 16

    def setUp(self):
        self.u = Axi_wDatapump(axiAddrCls=Axi3_addr)
        self.u.MAX_LEN.set(4)
        self.DATA_WIDTH = evalParam(self.u.DATA_WIDTH).val
        self.prepareUnit(self.u)

    def test_1024random(self):
        u = self.u
        req = u.driver._ag.req
        wIn = u.driver.w._ag
        dataMask = mask(self.DATA_WIDTH // 8)

        m = Axi3DenseMem(u.clk, axiAW=u.a, axiW=u.w, axiB=u.b)
        N = 1024
        data = [self._rand.getrandbits(self.DATA_WIDTH) for _ in range(N)]

        buff = m.malloc(N * (self.DATA_WIDTH // 8))

        dataIt = iter(data)
        end = False
        addr = 0
        while True:
            frameSize = self._rand.getrandbits(4) + 1
            frame = []
            try:
                for _ in range(frameSize):
                    frame.append(next(dataIt))
            except StopIteration:
                end = True

            if frame:
                req.data.append(req.mkReq(addr, len(frame) - 1))
                wIn.data.extend([(d, dataMask, i == len(frame) - 1)
                                 for i, d in enumerate(frame)])
                addr += len(frame) * self.DATA_WIDTH // 8
            if end:
                break

        ra = self.randomize
        ra(u.a)
        ra(u.b)
        ra(u.driver.req)
        ra(u.driver.ack)
        ra(u.w)
        ra(u.driver.w)

        self.doSim(N * 50 * Time.ns)

        inMem = m.getArray(buff, self.DATA_WIDTH // 8, N)
        self.assertValSequenceEqual(inMem, data)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi4_wDatapumpTC('test_multiple_randomized2'))
    suite.addTest(unittest.makeSuite(Axi4_wDatapumpTC))
    suite.addTest(unittest.makeSuite(Axi3_wDatapump_direct_TC))
    suite.addTest(unittest.makeSuite(Axi3_wDatapump_small_splitting_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
