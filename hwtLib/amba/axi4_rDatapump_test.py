#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi3 import Axi3_addr_withUser
from hwtLib.amba.axi4_rDatapump import Axi_rDatapump
from hwtLib.amba.constants import BURST_INCR, CACHE_DEFAULT, BYTES_IN_TRANS, \
    PROT_DEFAULT, LOCK_DEFAULT, QOS_DEFAULT, RESP_OKAY
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem


class Axi4_rDatapumpTC(SimTestCase):
    LEN_MAX = 255

    def setUp(self):
        self.u = Axi_rDatapump()
        self.prepareUnit(self.u)

    def mkDefaultAddrReq(self, _id, addr, _len):
        return (_id, addr, BURST_INCR, CACHE_DEFAULT, _len,
                LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS(8),
                QOS_DEFAULT)

    def test_nop(self):
        u = self.u
        self.doSim(200 * Time.ns)

        self.assertEmpty(u.a._ag.data)
        self.assertEmpty(u.driver.r._ag.data)

    def test_notSplitedReq(self):
        u = self.u

        req = u.driver._ag.req

        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, 0))
        self.doSim((self.LEN_MAX + 3) * Time.ns)

        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(u.a._ag.data), 1)
        self.assertEqual(len(u.driver._ag.r.data), 0)

    def test_notSplitedReqWithData(self):
        u = self.u

        req = u.driver.req._ag
        r = u.r._ag

        # download one word from addr 0xff
        req.data.append(req.mkReq(0xff, 0))
        for i in range(3):
            r.addData(i + 77)

        self.doSim((self.LEN_MAX + 3) * 10 * Time.ns)

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
        req.data.append(req.mkReq(0xff, LEN_MAX))
        for i in range(LEN_MAX + 1):
            r.addData(i + 77, last=(i == LEN_MAX))

        # dummy data
        r.addData(11)
        r.addData(12)

        self.doSim(((LEN_MAX + 6) * 10) * Time.ns)

        self.assertEmpty(req.data)
        self.assertEqual(len(u.a._ag.data), 1)

        # self.assertEqual(valuesToInts(u.driver._ag.r.data[0]), [77, mask(64 // 8), 0, 1])
        self.assertEqual(len(r.data), 2 - 1)  # no more data was taken
        self.assertValSequenceEqual(rout,
                                    [
                                     (0, 77 + i, mask(64 // 8), int(i == LEN_MAX))
                                     for i in range(LEN_MAX + 1)])
        self.assertEqual(len(r.data), 2 - 1)  # 2. is now sended

    def test_maxReq(self):
        u = self.u
        LEN_MAX = self.LEN_MAX

        req = u.driver.req._ag
        r = u.r._ag
        ar = u.a._ag.data
        rout = u.driver.r._ag.data

        # download 512 words from addr 0xff
        req.data.append(req.mkReq(0xff, 2 * LEN_MAX + 1))

        self.doSim(((LEN_MAX + 1) * 10) * Time.ns)

        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(rout), 0)

        _id = 0
        self.assertValSequenceEqual(ar,
                                    [
                                     self.mkDefaultAddrReq(_id, 0xff + (i * (LEN_MAX + 1) * 8), LEN_MAX)
                                     for i in range(2)
                                     ])

    def test_maxOverlap(self):
        u = self.u
        req = u.driver._ag.req
        ar = u.a._ag.data
        rout = u.driver.r._ag.data

        for i in range(32):
            req.data.append(req.mkReq(i, 0))
        #    r.addData(i + 77, last=(i == 255))

        self.doSim(((self.LEN_MAX + 6) * 10) * Time.ns)

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
            req.data.append(req.mkReq(i, 0))
            rdata = (_id, i + 1, RESP_OKAY, True)
            r.data.append(rdata)

        self.doSim(((64 + 4) * 10) * Time.ns)

        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(rout), 64)

        _id = 0
        _len = 0
        self.assertValSequenceEqual(ar,
                                    [self.mkDefaultAddrReq(_id, addr, _len)
                                        for addr in range(64)
                                     ])

    def test_multipleSplited(self):
        _id = 0
        FRAMES = 64
        l = self.LEN_MAX + 1

        u = self.u

        req = u.driver._ag.req
        r = u.r._ag
        ar = u.a._ag.data
        rout = u.driver.r._ag.data

        for i in range(FRAMES):
            req.data.append(req.mkReq(i, l, _id))
            for i2 in range(l + 1):
                isLast = (i2 > 0 and ((i2 % self.LEN_MAX) == 0) or (i2 == l))
                rdata = (_id, i2, RESP_OKAY, isLast)
                r.data.append(rdata)

        self.doSim(((len(r.data) + 4) * 10) * Time.ns)

        self.assertEqual(len(req.data), 0)
        self.assertEqual(len(ar), FRAMES * 2)
        self.assertEqual(len(rout), FRAMES * (l + 1))

        for i, arreq in enumerate(ar):
            if i % 2 == 0:
                addr = i // 2
                _len = self.LEN_MAX
            else:
                addr = (i // 2) + 8 * (self.LEN_MAX + 1)
                _len = 0

            self.assertValSequenceEqual(arreq,
                                        self.mkDefaultAddrReq(_id, addr, _len))

        _rout = iter(rout)

        for i in range(FRAMES):
            for i2 in range(l + 1):
                isLast = (i2 == l)
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
            req.data.append(req.mkReq(addr, len(data) - 1, _id=_id))
            expected = [
                        (_id, d, mask(8), i == len(data) - 1)
                          for i, d in enumerate(data)
                       ]
            return expected

        expected = []
        for _ in range(24):
            size = int(self._rand.random() * self.LEN_MAX)+1
            a = m.malloc(size)
            indx = a // m.cellSize
            data = []

            for i2 in range(size):
                data.append(MAGIC)
                m.data[indx + i2] = MAGIC
                MAGIC += i2

            e = prepareRequest(1, a, data)
            expected.extend(e)

        self.doSim(len(expected) * 70 * Time.ns)

        self.assertEmpty(u.driver.req._ag.data)
        self.assertValSequenceEqual(u.driver.r._ag.data, expected)


class Axi3_rDatapumpTC(Axi4_rDatapumpTC):
    LEN_MAX = 15

    def setUp(self):
        self.u = Axi_rDatapump(axiAddrCls=Axi3_addr_withUser)
        self.prepareUnit(self.u)

    def mkDefaultAddrReq(self, _id, addr, _len):
        return (_id, addr, BURST_INCR, CACHE_DEFAULT, _len,
                LOCK_DEFAULT, PROT_DEFAULT, BYTES_IN_TRANS(8),
                QOS_DEFAULT, 0)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(Axi3_rDatapumpTC('test_randomized'))
    # suite.addTest(unittest.makeSuite(Axi3_rDatapumpTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
