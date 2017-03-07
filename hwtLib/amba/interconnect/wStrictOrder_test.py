#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.param import evalParam
from hwtLib.abstract.denseMemory import DenseMemory
from hwtLib.amba.interconnect.wStrictOrder import WStrictOrderInterconnect


class WStrictOrderInterconnectTC(SimTestCase):
    def setUp(self):
        super(WStrictOrderInterconnectTC, self).setUp()
        self.u = WStrictOrderInterconnect()
        self.MAX_TRANS_OVERLAP = 4
        self.u.MAX_TRANS_OVERLAP.set(self.MAX_TRANS_OVERLAP)
        self.DATA_WIDTH = evalParam(self.u.DATA_WIDTH).val

        self.DRIVER_CNT = 2
        self.u.DRIVER_CNT.set(self.DRIVER_CNT)
        _, self.model, self.procs = simPrepare(self.u)

    def test_nop(self):
        u = self.u
        self.doSim(200 * Time.ns)

        for d in u.drivers:
            self.assertEqual(len(d.ack._ag.data), 0)

        self.assertEmpty(u.wDatapump.req._ag.data)
        self.assertEmpty(u.wDatapump.w._ag.data)

    def test_passReq(self):
        u = self.u

        for i, driver in enumerate(u.drivers):
            driver.req._ag.data.append((i + 1, i + 1, i + 1, 0))

        self.doSim(40 * Time.ns)

        self.assertEmpty(u.wDatapump.w._ag.data)

        req = u.wDatapump.req._ag.data
        expectedReq = [(i + 1, i + 1, i + 1, 0) for i in range(2)]
        self.assertValSequenceEqual(req, expectedReq)

    def test_passData(self):
        u = self.u
        expectedW = []

        for i, driver in enumerate(u.drivers):
            _id = i + 1
            _len = i + 1
            driver.req._ag.data.append((_id, i + 1, _len, 0))
            strb = mask(self.DATA_WIDTH // 8)
            for i2 in range(_len + 1):
                _data = i + i2 + 1
                last = int(i2 == _len)
                d = (_data, strb, last)
                driver.w._ag.data.append(d)
                expectedW.append(d)

        self.doSim(80 * Time.ns)

        req = u.wDatapump.req._ag.data
        wData = u.wDatapump.w._ag.data

        for i, _req in enumerate(req):
            self.assertValSequenceEqual(_req,
                                        (i + 1, i + 1, i + 1, 0))

        self.assertEqual(len(req), self.DRIVER_CNT)

        for w, expW in zip(wData, expectedW):
            self.assertValSequenceEqual(w, expW)

    def test_randomized(self):
        u = self.u
        m = DenseMemory(self.DATA_WIDTH, u.clk, wDatapumpIntf=u.wDatapump)

        for d in u.drivers:
            self.randomize(d.req)
            self.randomize(d.w)
            self.randomize(d.ack)

        self.randomize(u.wDatapump.req)
        self.randomize(u.wDatapump.w)
        self.randomize(u.wDatapump.ack)

        sectors = []

        def prepare(driverIndex, addr, size, valBase=1, _id=1):
            driver = u.drivers[driverIndex]
            driver.req._ag.data.append((_id, addr, size - 1, 0))
            _mask = mask(self.DATA_WIDTH // 8)

            for i in range(size):
                d = (valBase + i, _mask, int(i == size - 1))

                driver.w._ag.data.append(d)
                u.wDatapump.ack._ag.data.append(driverIndex)

            sectors.append((addr, valBase, size))

        prepare(0, 0x1000, 3, 99, _id=0)
        prepare(0, 0x2000, 1, 100, _id=0)
        prepare(0, 0x3000, 16, 101)
        prepare(1, 0x4000, 3, 200, _id=1)
        prepare(1, 0x5000, 1, 201, _id=1)  # + prepare(1, 0x6000, 16, 202) #+ prepare(1, 0x7000, 16, 203)

        self.doSim(2000 * Time.ns)

        for addr, seed, size in sectors:
            expected = [seed + i for i in range(size)]
            self.assertValSequenceEqual(m.getArray(addr, 8, size), expected)

    def test_randomized2(self):
        u = self.u
        m = DenseMemory(self.DATA_WIDTH, u.clk, wDatapumpIntf=u.wDatapump)
        N = 25
        _mask = mask(self.DATA_WIDTH // 8)

        for d in u.drivers:
            self.randomize(d.req)
            self.randomize(d.w)
            self.randomize(d.ack)

        self.randomize(u.wDatapump.req)
        self.randomize(u.wDatapump.w)
        self.randomize(u.wDatapump.ack)

        sectors = []
        framesCnt = [0 for _ in range(self.DRIVER_CNT)]
        for i in range(N):
            for _id, d in enumerate(u.drivers):
                size = self._rand.getrandbits(3) + 1
                magic = self._rand.getrandbits(16)
                addr = m.calloc(size, 8, initValues=[None for _ in range(size)])

                d.req._ag.data.append((_id, addr, size - 1, 0))
                for i in range(size):
                    data = (magic + i, _mask, int(i == size - 1))
                    d.w._ag.data.append(data)

                values = [i + magic for i in range(size)]
                sectors.append((_id, addr, values))
                framesCnt[_id] += 1

        self.doSim(self.DRIVER_CNT * N * 250 * Time.ns)

        for _id, d in enumerate(u.drivers):
            self.assertEmpty(d.req._ag.data)
            self.assertEmpty(d.w._ag.data)
            self.assertEquals(len(u.drivers[_id].ack._ag.data),
                              framesCnt[_id])

        for _id, addr, expected in sectors:
            v = m.getArray(addr, 8, len(expected))
            self.assertSequenceEqual(v, expected)

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(WStrictOrderInterconnectTC('test_randomized'))
    suite.addTest(unittest.makeSuite(WStrictOrderInterconnectTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
