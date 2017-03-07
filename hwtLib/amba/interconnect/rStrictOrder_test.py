#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.denseMemory import DenseMemory
from hwtLib.amba.interconnect.rStricOrder import RStrictOrderInterconnect


class RStrictOrderInterconnectTC(SimTestCase):
    def setUp(self):
        super(RStrictOrderInterconnectTC, self).setUp()
        u = self.u = RStrictOrderInterconnect()

        self.DRIVERS_CNT = 3
        u.DRIVER_CNT.set(self.DRIVERS_CNT)

        self.MAX_TRANS_OVERLAP = 4
        u.MAX_TRANS_OVERLAP.set(self.MAX_TRANS_OVERLAP)

        self.DATA_WIDTH = 64
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        _, self.model, self.procs = simPrepare(self.u)

    def test_nop(self):
        u = self.u
        self.doSim(200 * Time.ns)

        for d in u.drivers:
            self.assertEqual(len(d.r._ag.data), 0)

        self.assertEqual(len(u.rDatapump.req._ag.data), 0)

    def test_passWithouData(self):
        u = self.u

        for i, driver in enumerate(u.drivers):
            driver.req._ag.data.append((i + 1, i + 1, i + 1, 0))

        self.doSim((self.DRIVERS_CNT * 20) * Time.ns)

        for d in u.drivers:
            self.assertEqual(len(d.r._ag.data), 0)

        self.assertEqual(len(u.rDatapump.req._ag.data), self.DRIVERS_CNT)
        for i, req in enumerate(u.rDatapump.req._ag.data):
            self.assertValSequenceEqual(req,
                                        (i + 1, i + 1, i + 1, 0))

    def test_passWithData(self):
        u = self.u

        for i, driver in enumerate(u.drivers):
            _id = i + 1
            _len = i + 1
            driver.req._ag.data.append((_id, i + 1, _len, 0))
            for i2 in range(_len + 1):
                d = (_id, i + 1, mask(self.DATA_WIDTH), i2 == _len)
                u.rDatapump.r._ag.data.append(d)

        self.doSim(200 * Time.ns)

        for i, d in enumerate(u.drivers):
            self.assertEqual(len(d.r._ag.data), i + 1 + 1)

        self.assertEqual(len(u.rDatapump.req._ag.data), self.DRIVERS_CNT)
        for i, req in enumerate(u.rDatapump.req._ag.data):
            self.assertValSequenceEqual(req,
                                        (i + 1, i + 1, i + 1, 0))

    def test_randomized(self):
        u = self.u
        m = DenseMemory(self.DATA_WIDTH, u.clk, u.rDatapump)

        for d in u.drivers:
            self.randomize(d.req)
            self.randomize(d.r)
        self.randomize(u.rDatapump.req)
        self.randomize(u.rDatapump.r)

        def prepare(driverIndex, addr, size, valBase=1, _id=1):
            driver = u.drivers[driverIndex]
            driver.req._ag.data.append((_id, addr, size - 1, 0))
            expected = []
            _mask = mask(self.DATA_WIDTH // 8)
            index = addr // (self.DATA_WIDTH // 8)
            for i in range(size):
                v = valBase + i
                m.data[index + i] = v
                d = (_id, v, _mask, int(i == size - 1))
                expected.append(d)
            return expected

        def check(driverIndex, expected):
            driverData = u.drivers[driverIndex].r._ag.data
            self.assertEqual(len(driverData), len(expected))
            for d, e in zip(driverData, expected):
                self.assertValSequenceEqual(d, e)

        d0 = prepare(0, 0x1000, 3, 99, _id=0)  # + prepare(0, 0x2000, 1, 100, _id=0) + prepare(0, 0x3000, 16, 101)
        d1 = prepare(1, 0x4000, 3, 200, _id=1) + prepare(1, 0x5000, 1, 201, _id=1)  # + prepare(1, 0x6000, 16, 202) #+ prepare(1, 0x7000, 16, 203)

        self.doSim(1000 * Time.ns)

        check(0, d0)
        check(1, d1)

    def test_randomized2(self):
        u = self.u
        m = DenseMemory(self.DATA_WIDTH, u.clk, u.rDatapump)
        N = 17

        for d in u.drivers:
            self.randomize(d.req)
            self.randomize(d.r)
        self.randomize(u.rDatapump.req)
        self.randomize(u.rDatapump.r)
        _mask = mask(self.DATA_WIDTH // 8)

        expected = [[] for _ in u.drivers]
        for _id, d in enumerate(u.drivers):
            for i in range(N):
                size = self._rand.getrandbits(3) + 1
                magic = self._rand.getrandbits(16)
                values = [i + magic for i in range(size)]
                addr = m.calloc(size, 8, initValues=values)

                d.req._ag.data.append((_id, addr, size - 1, 0))

                for i2, v in enumerate(values):
                    data = (_id, v, _mask, int(i2 == size - 1))
                    expected[_id].append(data)

        self.doSim(self.DRIVERS_CNT * N * 200 * Time.ns)

        for expect, driver in zip(expected, u.drivers):
            self.assertValSequenceEqual(driver.r._ag.data, expect)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(RStrictOrderInterconnectTC('test_passWithouData'))
    suite.addTest(unittest.makeSuite(RStrictOrderInterconnectTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
