#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.amba.axi3 import Axi3_addr, Axi3_w
from hwtLib.amba.axi4 import Axi4_addr
from hwtLib.amba.axi_comp.axi4_rDatapump_test import Axi4_rDatapumpTC, mkReq
from hwtLib.amba.axi_comp.axi4_wDatapump import Axi_wDatapump
from hwtLib.amba.constants import RESP_OKAY, BYTES_IN_TRANS, BURST_INCR, \
    CACHE_DEFAULT, LOCK_DEFAULT, PROT_DEFAULT, QOS_DEFAULT
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem
from pyMathBitPrecise.bit_utils import mask
from pycocotb.constants import CLK_PERIOD


class Axi4_wDatapumpTC(SingleUnitSimTestCase):
    LEN_MAX = Axi4_rDatapumpTC.LEN_MAX

    @classmethod
    def getUnit(cls):
        cls.u = u = Axi_wDatapump(axiAddrCls=Axi4_addr)
        u.MAX_LEN = cls.LEN_MAX
        return cls.u

    def aTrans(self, id_, addr, len_, burst=BURST_INCR, cache=CACHE_DEFAULT,
               lock=LOCK_DEFAULT, prot=PROT_DEFAULT, size=BYTES_IN_TRANS(8),
               qos=QOS_DEFAULT):
        return (id_, addr, burst, cache, len_, lock, prot, size, qos)

    def wTrans(self, data, last, strb=mask(64 // 8), id_=0):
        return (data, strb, last)

    def test_nop(self):
        u = self.u

        self.runSim(20 * CLK_PERIOD)

        self.assertEmpty(u.a._ag.data)
        self.assertEmpty(u.w._ag.data)

    def test_simple(self):
        u = self.u

        req = u.driver._ag.req
        aw = u.a._ag.data

        # download one word from addr 0xff
        req.data.append(mkReq(0xff, 0))

        self.runSim(20 * CLK_PERIOD)

        self.assertValSequenceEqual(aw,
                                    [
                                        self.aTrans(0, 255, 0)
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
        req.data.append(mkReq(0xff, 0))
        wIn.data.append((77, mask(64 // 8), 1))
        b.append((0, RESP_OKAY))

        self.runSim(20 * CLK_PERIOD)

        self.assertValSequenceEqual(aw, [
            self.aTrans(0, 255, 0)
        ])

        self.assertValSequenceEqual(
            w, [self.wTrans(77, 1, strb=mask(64 // 8), id_=0)])
        self.assertEmpty(b)

    def test_singleLong(self):
        u = self.u

        req = u.driver._ag.req
        aw = u.a._ag.data
        wIn = u.driver.w._ag
        w = u.w._ag.data
        b = u.b._ag.data

        # download one word from addr 0xff
        req.data.append(mkReq(0xff, self.LEN_MAX))
        for i in range(self.LEN_MAX + 1 + 10):
            wIn.data.append((100 + 1, mask(8), i == self.LEN_MAX))
        b.append((0, RESP_OKAY))

        self.runSim((10 + self.LEN_MAX) * CLK_PERIOD)

        self.assertValSequenceEqual(aw,
                                    [
                                        self.aTrans(
                                            id_=0,
                                            addr=0xff,
                                            len_=self.LEN_MAX)
                                    ])

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
            req.data.append(mkReq((i * 8) + 0xff, 0))
            wIn.data.append((77, mask(64 // 8), 1))
            b.append((0, RESP_OKAY))

        self.runSim(100 * CLK_PERIOD)

        self.assertValSequenceEqual(aw,
                                    [
                                        self.aTrans(
                                            id_=0, addr=0xff + (8 * i), len_=0)
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
            req.data.append(mkReq((i * 8) + 0xff, 0))
            wIn.data.append((77, mask(64 // 8 - 1), 1))
            b.append((0, RESP_OKAY))

        ra = self.randomize
        ra(u.a)
        ra(u.b)
        ra(u.driver.req)
        ra(u.driver.ack)
        ra(u.w)
        ra(u.driver.w)

        self.runSim(N * 8 * CLK_PERIOD)

        self.assertValSequenceEqual(aw,
                                    [
                                        self.aTrans(
                                            id_=0, addr=0xff + (8 * i), len_=0)
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
            req.data.append(mkReq((i * 8) + 0xff, L - 1))
            for i in range(L):
                d = 77 + i
                m = mask(64 // 8 - 1)
                last = int(i == (L - 1))
                wIn.data.append((d, m, last))
                beat = self.wTrans(d, last, strb=m, id_=0)

                expectedWData.append(beat)
            b.append((0, RESP_OKAY))

        ra = self.randomize
        ra(u.a)
        ra(u.b)
        ra(u.driver.req)
        ra(u.driver.ack)
        ra(u.w)
        ra(u.driver.w)

        self.runSim(N * L * 5 * CLK_PERIOD)

        self.assertValSequenceEqual(aw,
                                    [
                                        self.aTrans(
                                            id_=0,
                                            addr=0xff + (8 * i),
                                            len_=L - 1)
                                        for i in range(N)
                                    ])

        self.assertEqual(len(w), N * 3)
        for expWD, wd in zip(expectedWData, w):
            self.assertValSequenceEqual(wd, expWD)

        self.assertEqual(len(b), 0)
        self.assertEqual(len(u.driver._ag.ack.data), N)


class Axi3_wDatapump_direct_TC(Axi4_wDatapumpTC):
    LEN_MAX = 15

    def aTrans(self, id_, addr, len_, burst=BURST_INCR, cache=CACHE_DEFAULT,
               lock=LOCK_DEFAULT, prot=PROT_DEFAULT, size=BYTES_IN_TRANS(8),
               qos=QOS_DEFAULT):
        return (id_, addr, burst, cache, len_, lock, prot, size)

    def wTrans(self, data, last, strb=mask(64 // 8), id_=0):
        return (id_, data, strb, last)

    @classmethod
    def getUnit(cls):
        u = Axi_wDatapump(axiAddrCls=Axi3_addr, axiWCls=Axi3_w)
        u.MAX_LEN = 16
        return u


class Axi3_wDatapump_small_splitting_TC(SingleUnitSimTestCase):
    LEN_MAX = 3

    def aTrans(self, id_, addr, len_, burst=BURST_INCR, cache=CACHE_DEFAULT,
               lock=LOCK_DEFAULT, prot=PROT_DEFAULT, size=BYTES_IN_TRANS(8),
               qos=QOS_DEFAULT):
        return (id_, addr, burst, cache, len_, lock, prot, size)

    def wTrans(self, data, last, strb=mask(64 // 8), id_=0):
        return (id_, data, strb, last)

    @classmethod
    def getUnit(cls):
        u = cls.u = Axi_wDatapump(axiAddrCls=Axi3_addr, axiWCls=Axi3_w)
        u.MAX_LEN = cls.LEN_MAX
        cls.DATA_WIDTH = int(u.DATA_WIDTH)
        return u

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
            frameSize = self._rand.getrandbits(self.LEN_MAX.bit_length()) + 1
            frame = []
            try:
                for _ in range(frameSize):
                    frame.append(next(dataIt))
            except StopIteration:
                end = True

            if frame:
                req.data.append(mkReq(addr, len(frame) - 1))
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

        self.runSim(N * 5 * CLK_PERIOD)

        inMem = m.getArray(buff, self.DATA_WIDTH // 8, N)
        self.assertValSequenceEqual(inMem, data)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi4_wDatapumpTC('test_singleLong'))
    suite.addTest(unittest.makeSuite(Axi4_wDatapumpTC))
    suite.addTest(unittest.makeSuite(Axi3_wDatapump_direct_TC))
    suite.addTest(unittest.makeSuite(Axi3_wDatapump_small_splitting_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
