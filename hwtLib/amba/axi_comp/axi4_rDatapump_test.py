#!/usr/bin/env python3e
# -*- coding: utf-8 -*-


from hwt.simulator.simTestCase import SimTestCase, SingleUnitSimTestCase
from hwtLib.amba.axi3 import Axi3_addr
from hwtLib.amba.axi4 import Axi4_addr
from hwtLib.amba.axi_comp.axi4_rDatapump import Axi_rDatapump
from hwtLib.amba.constants import BURST_INCR, CACHE_DEFAULT, BYTES_IN_TRANS, \
    PROT_DEFAULT, LOCK_DEFAULT, QOS_DEFAULT, RESP_OKAY
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem
from pyMathBitPrecise.bit_utils import mask
from pycocotb.constants import CLK_PERIOD


def mkReq(addr, _len, rem=0, _id=0):
    return (_id, addr, _len, rem)


def mkReqAxi(addr, _len, _id=0,
             burst=BURST_INCR,
             cache=CACHE_DEFAULT,
             lock=LOCK_DEFAULT,
             prot=PROT_DEFAULT,
             size=BYTES_IN_TRANS(8),
             qos=QOS_DEFAULT):

    return (_id, addr, burst, cache, _len, lock, prot, size, qos)


def addData(ag, data, _id=0, resp=RESP_OKAY, last=True):
    ag.data.append((_id, data, resp, last))


class Axi4_rDatapumpTC(SingleUnitSimTestCase):
    LEN_MAX = 255
    DATA_WIDTH = 64

    @classmethod
    def getUnit(cls):
        cls.u = Axi_rDatapump(axiAddrCls=Axi4_addr)
        cls.u.DATA_WIDTH = cls.DATA_WIDTH
        return cls.u

    def mkDefaultAddrReq(self, _id, addr, _len):
        return (_id, addr, BURST_INCR, CACHE_DEFAULT, _len,
                LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS(8),
                QOS_DEFAULT)

    def test_nop(self):
        u = self.u
        self.runSim(20 * CLK_PERIOD)

        self.assertEmpty(u.a._ag.data)
        self.assertEmpty(u.driver.r._ag.data)

    def test_notSplitedReq(self):
        u = self.u

        req = u.driver._ag.req

        # download one word from addr 0xff
        req.data.append(mkReq(0xff, 0))
        self.runSim((self.LEN_MAX + 3) * CLK_PERIOD)

        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(u.a._ag.data), 1)
        self.assertEqual(len(u.driver._ag.r.data), 0)

    def test_notSplitedReqWithData(self):
        u = self.u

        req = u.driver.req._ag
        r = u.r._ag

        # download one word from addr 0xff
        req.data.append(mkReq(0xff, 0))
        for i in range(3):
            addData(r, i + 77)

        self.runSim((self.LEN_MAX + 3) * CLK_PERIOD)

        self.assertEmpty(req.data)
        self.assertEqual(len(u.a._ag.data), 1)
        self.assertValSequenceEqual(u.driver._ag.r.data,
                                    [
                                        (0, 77, mask(64 // 8), 1)
                                    ])
        self.assertEqual(len(r.data), 2 - 1)  # 2. is now sended

    def test_maxNotSplitedReqWithData(self):
        u = self.u
        LEN_MAX = self.LEN_MAX

        req = u.driver.req._ag
        r = u.r._ag
        rout = u.driver.r._ag.data

        # download 256 words from addr 0xff
        req.data.append(mkReq(0xff, LEN_MAX))
        for i in range(LEN_MAX + 1):
            addData(r, i + 77, last=(i == LEN_MAX))

        # dummy data
        addData(r, 11)
        addData(r, 12)

        self.runSim((LEN_MAX + 6) * CLK_PERIOD)

        self.assertEmpty(req.data)
        self.assertEqual(len(u.a._ag.data), 1)

        # self.assertEqual(valuesToInts(u.driver._ag.r.data[0]),
        # [77, mask(64 // 8), 0, 1])
        self.assertEqual(len(r.data), 2 - 1)  # no more data was taken
        self.assertValSequenceEqual(rout,
                                    [(0, 77 + i, mask(64 // 8),
                                      int(i == LEN_MAX))
                                     for i in range(LEN_MAX + 1)])
        self.assertEqual(len(r.data), 2 - 1)  # 2. is now sended

    def test_maxReq(self):
        u = self.u
        LEN_MAX = self.LEN_MAX

        req = u.driver.req._ag
        ar = u.a._ag.data
        rout = u.driver.r._ag.data

        # download 512 words from addr 0xff
        req.data.append(mkReq(0xff, 2 * LEN_MAX + 1))

        self.runSim((LEN_MAX + 1) * CLK_PERIOD)

        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(rout), 0)

        _id = 0
        self.assertValSequenceEqual(ar,
                                    [
                                        self.mkDefaultAddrReq(
                                            _id, 0xff +
                                            (i * (LEN_MAX + 1) * 8),
                                            LEN_MAX)
                                        for i in range(2)
                                    ])

    def test_maxOverlap(self):
        u = self.u
        req = u.driver._ag.req
        ar = u.a._ag.data
        rout = u.driver.r._ag.data

        for i in range(32):
            req.data.append(mkReq(i, 0))
        #    r.addData(i + 77, last=(i == 255))

        self.runSim((self.LEN_MAX + 6) * CLK_PERIOD)

        self.assertEqual(len(req.data), 15)
        self.assertEqual(len(rout), 0)

        _id = 0
        _len = 0
        self.assertValSequenceEqual(ar,
                                    [self.mkDefaultAddrReq(_id, addr, _len)
                                        for addr in range(16)
                                     ])

    def test_multipleShortest(self):
        u = self.u
        _id = 0

        req = u.driver._ag.req
        r = u.r._ag
        ar = u.a._ag.data
        rout = u.driver.r._ag.data

        for i in range(64):
            req.data.append(mkReq(i, 0))
            rdata = (_id, i + 1, RESP_OKAY, True)
            r.data.append(rdata)

        self.runSim((64 + 4) * CLK_PERIOD)

        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(rout), 64)

        _id = 0
        _len = 0
        self.assertValSequenceEqual(ar,
                                    [self.mkDefaultAddrReq(_id, addr, _len)
                                        for addr in range(64)
                                     ])

    def test_endstrb(self):
        u = self.u
        _id = 0
        # MAGIC = self._rand.getrandbits(16)

        req = u.driver._ag.req
        r = u.r._ag
        ar = u.a._ag.data
        rout = u.driver.r._ag.data

        expected = []
        for i in range(self.DATA_WIDTH // 8):
            req.data.append(mkReq(i * (self.DATA_WIDTH // 8), 0, rem=i))
            _len = 1
            for i2 in range(_len):
                isLast = int(i2 == _len - 1)
                r.data.append((_id, i2 + 1, RESP_OKAY, isLast))
                if not isLast or i == 0:
                    m = mask(self.DATA_WIDTH // 8)
                else:
                    m = mask(i)
                expected.append((_id, i2 + 1, m, isLast))

        self.runSim(len(expected) * 2 * CLK_PERIOD)

        self.assertEmpty(req.data)

        _id = 0
        _len = 0
        self.assertValSequenceEqual(ar,
                                    [self.mkDefaultAddrReq(
                                        _id,
                                        i * (self.DATA_WIDTH // 8),
                                        0)
                                        for i in range(self.DATA_WIDTH // 8)
                                     ])
        self.assertValSequenceEqual(rout, expected)

    def test_endstrbMultiFrame(self):
        u = self.u
        _id = 0
        # MAGIC = self._rand.getrandbits(16)

        req = u.driver._ag.req
        r = u.r._ag
        ar = u.a._ag.data
        rout = u.driver.r._ag.data
        lastRem = (self.DATA_WIDTH // 8) - 1

        expected = []
        _len = self.LEN_MAX + 3
        req.data.append(mkReq(0, _len - 1, rem=lastRem))
        for i2 in range(self.LEN_MAX + 3):
            isLast = int(i2 == _len - 1)
            isLastOnBus = isLast or (i2 == self.LEN_MAX)

            r.data.append((_id, i2 + 1, RESP_OKAY, isLastOnBus))
            if isLast:
                m = mask(lastRem)
            else:
                m = mask(self.DATA_WIDTH // 8)

            expected.append((_id, i2 + 1, m, isLast))

        self.runSim(len(expected) * 2 * CLK_PERIOD)

        self.assertEmpty(req.data)

        _id = 0
        _mkReq = self.mkDefaultAddrReq
        self.assertValSequenceEqual(ar,
                                    [_mkReq(_id, 0, self.LEN_MAX),
                                     _mkReq(_id, (self.LEN_MAX + 1) *
                                            (self.DATA_WIDTH // 8), 1)
                                     ])
        self.assertValSequenceEqual(rout, expected)

    def test_multipleSplited(self):
        _id = 0
        FRAMES = 64
        _len = self.LEN_MAX + 1

        u = self.u

        req = u.driver._ag.req
        r = u.r._ag
        ar = u.a._ag.data
        rout = u.driver.r._ag.data

        for i in range(FRAMES):
            req.data.append(mkReq(i, _len, _id))
            for i2 in range(_len + 1):
                isLast = (i2 > 0 and ((i2 % self.LEN_MAX) == 0)
                          or (i2 == _len))
                rdata = (_id, i2, RESP_OKAY, isLast)
                r.data.append(rdata)

        self.runSim((len(r.data) + 4) * CLK_PERIOD)

        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(ar), FRAMES * 2)
        self.assertEqual(len(rout), FRAMES * (_len + 1))

        for i, arreq in enumerate(ar):
            if i % 2 == 0:
                addr = i // 2
                len_tmp = self.LEN_MAX
            else:
                addr = (i // 2) + 8 * (self.LEN_MAX + 1)
                len_tmp = 0

            self.assertValSequenceEqual(arreq,
                                        self.mkDefaultAddrReq(_id,
                                                              addr,
                                                              len_tmp))

        _rout = iter(rout)

        for i in range(FRAMES):
            for i2 in range(_len + 1):
                isLast = (i2 == _len)
                rdata = (_id, i2, mask(8), isLast)
                d = next(_rout)
                self.assertValSequenceEqual(d, rdata)

    def test_randomized(self):
        u = self.u

        m = Axi3DenseMem(u.clk, axiAR=u.a, axiR=u.r)
        MAGIC = 99
        req = u.driver.req._ag

        self.randomize(u.driver.r)
        self.randomize(u.driver.req)

        self.randomize(u.a)
        self.randomize(u.r)

        def prepareRequest(_id, addr, data):
            req.data.append(mkReq(addr, len(data) - 1, _id=_id))
            expected = [
                (_id, d, mask(8), i == len(data) - 1)
                for i, d in enumerate(data)
            ]
            return expected

        expected = []
        for _ in range(24):
            size = int(self._rand.random() * self.LEN_MAX) + 1
            a = m.malloc(size)
            indx = a // m.cellSize
            data = []

            for i2 in range(size):
                data.append(MAGIC)
                m.data[indx + i2] = MAGIC
                MAGIC += i2

            e = prepareRequest(1, a, data)
            expected.extend(e)

        self.runSim(len(expected) * 7 * CLK_PERIOD)

        self.assertEmpty(u.driver.req._ag.data)
        self.assertValSequenceEqual(u.driver.r._ag.data, expected)


class Axi3_rDatapumpTC(Axi4_rDatapumpTC):
    LEN_MAX = 15

    @classmethod
    def getUnit(cls):
        cls.u = Axi_rDatapump(axiAddrCls=Axi3_addr)
        cls.u.DATA_WIDTH = cls.DATA_WIDTH
        return cls.u

    def mkDefaultAddrReq(self, _id, addr, _len):
        return (_id, addr, BURST_INCR, CACHE_DEFAULT, _len,
                LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS(8))


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi3_rDatapumpTC('test_endstrbMultiFrame'))
    suite.addTest(unittest.makeSuite(Axi3_rDatapumpTC))
    suite.addTest(unittest.makeSuite(Axi4_rDatapumpTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
