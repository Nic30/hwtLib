#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.datapump.interconnect.wStrictOrder import WStrictOrderInterconnect
from hwtLib.amba.datapump.sim_ram import AxiDpSimRam
from pyMathBitPrecise.bit_utils import mask


def mkReq(addr, _len, rem=0, _id=0):
    return (_id, addr, _len, rem)


class WStrictOrderInterconnectTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = WStrictOrderInterconnect()
        dut.MAX_TRANS_OVERLAP = cls.MAX_TRANS_OVERLAP = 4
        cls.DATA_WIDTH = dut.DATA_WIDTH
        dut.DRIVER_CNT = cls.DRIVER_CNT = 2
        cls.compileSim(dut)

    def test_nop(self):
        dut = self.dut
        self.runSim(200 * Time.ns)

        for d in dut.drivers:
            self.assertEqual(len(d.ack._ag.data), 0)

        self.assertEmpty(dut.wDatapump.req._ag.data)
        self.assertEmpty(dut.wDatapump.w._ag.data)

    def test_passReq(self):
        dut = self.dut

        for i, driver in enumerate(dut.drivers):
            driver.req._ag.data.append((i + 1, i + 1, i + 1, 0))

        self.runSim(40 * Time.ns)

        self.assertEmpty(dut.wDatapump.w._ag.data)

        req = dut.wDatapump.req._ag.data
        expectedReq = [(i + 1, i + 1, i + 1, 0) for i in range(2)]
        self.assertValSequenceEqual(req, expectedReq)

    def test_passData(self):
        dut = self.dut
        expectedW = []

        for i, driver in enumerate(dut.drivers):
            _id = i + 1
            _len = i + 1
            driver.req._ag.data.append((_id, i + 1, _len, 0))
            strb = mask(dut.DATA_WIDTH // 8)
            for i2 in range(_len + 1):
                _data = i + i2 + 1
                last = int(i2 == _len)
                d = (_data, strb, last)
                driver.w._ag.data.append(d)
                expectedW.append(d)

        self.runSim(80 * Time.ns)

        req = dut.wDatapump.req._ag.data
        wData = dut.wDatapump.w._ag.data

        for i, _req in enumerate(req):
            self.assertValSequenceEqual(_req,
                                        (i + 1, i + 1, i + 1, 0))

        self.assertEqual(len(req), self.DRIVER_CNT)

        for w, expW in zip(wData, expectedW):
            self.assertValSequenceEqual(w, expW)

    def test_randomized(self):
        dut = self.dut
        m = AxiDpSimRam(dut.DATA_WIDTH, dut.clk, wDatapumpHwIO=dut.wDatapump)

        for d in dut.drivers:
            self.randomize(d.req)
            self.randomize(d.w)
            self.randomize(d.ack)

        self.randomize(dut.wDatapump.req)
        self.randomize(dut.wDatapump.w)
        self.randomize(dut.wDatapump.ack)

        sectors = []

        def prepare(driverIndex, addr, size, valBase=1, _id=1):
            driver = dut.drivers[driverIndex]
            driver.req._ag.data.append((_id, addr, size - 1, 0))
            _mask = mask(dut.DATA_WIDTH // 8)

            for i in range(size):
                d = (valBase + i, _mask, int(i == size - 1))

                driver.w._ag.data.append(d)
                dut.wDatapump.ack._ag.data.append(driverIndex)

            sectors.append((addr, valBase, size))

        prepare(0, 0x1000, 3, 99, _id=0)
        prepare(0, 0x2000, 1, 100, _id=0)
        prepare(0, 0x3000, 16, 101)
        prepare(1, 0x4000, 3, 200, _id=1)
        prepare(1, 0x5000, 1, 201, _id=1)
        # + prepare(1, 0x6000, 16, 202) #+ prepare(1, 0x7000, 16, 203)

        self.runSim(2000 * Time.ns)

        for addr, seed, size in sectors:
            expected = [seed + i for i in range(size)]
            self.assertValSequenceEqual(m.getArray(addr, dut.DATA_WIDTH // 8, size), expected)

    def test_randomized2(self):
        dut = self.dut
        m = AxiDpSimRam(dut.DATA_WIDTH, dut.clk, wDatapumpHwIO=dut.wDatapump)
        N = 25
        _mask = mask(dut.DATA_WIDTH // 8)

        for d in dut.drivers:
            self.randomize(d.req)
            self.randomize(d.w)
            self.randomize(d.ack)

        self.randomize(dut.wDatapump.req)
        self.randomize(dut.wDatapump.w)
        self.randomize(dut.wDatapump.ack)

        sectors = []
        framesCnt = [0 for _ in range(self.DRIVER_CNT)]
        for i in range(N):
            for _id, d in enumerate(dut.drivers):
                size = self._rand.getrandbits(3) + 1
                magic = self._rand.getrandbits(16)
                addr = m.calloc(size, dut.DATA_WIDTH // 8,
                                initValues=[None for _ in range(size)])

                d.req._ag.data.append((_id, addr, size - 1, 0))
                for i in range(size):
                    data = (magic + i, _mask, int(i == size - 1))
                    d.w._ag.data.append(data)

                values = [i + magic for i in range(size)]
                sectors.append((_id, addr, values))
                framesCnt[_id] += 1

        self.runSim(self.DRIVER_CNT * N * 250 * Time.ns)

        for _id, d in enumerate(dut.drivers):
            self.assertEmpty(d.req._ag.data)
            self.assertEmpty(d.w._ag.data)
            self.assertEqual(len(dut.drivers[_id].ack._ag.data),
                             framesCnt[_id])

        for _id, addr, expected in sectors:
            v = m.getArray(addr, dut.DATA_WIDTH // 8, len(expected))
            self.assertSequenceEqual(v, expected)


class WStrictOrderInterconnect2TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = WStrictOrderInterconnect()
        dut.MAX_TRANS_OVERLAP = cls.MAX_TRANS_OVERLAP = 4
        cls.DATA_WIDTH = dut.DATA_WIDTH = 64
        dut.DRIVER_CNT = cls.DRIVER_CNT = 3
        cls.compileSim(dut)

    def test_3x128(self):
        dut = self.dut
        m = AxiDpSimRam(dut.DATA_WIDTH, dut.clk, wDatapumpHwIO=dut.wDatapump)
        N = 128
        _mask = mask(dut.DATA_WIDTH // 8)
        data = [[self._rand.getrandbits(dut.DATA_WIDTH) for _ in range(N)]
                for _ in range(self.DRIVER_CNT)]

        dataAddress = [m.malloc(N * dut.DATA_WIDTH // 8)
                       for _ in range(self.DRIVER_CNT)]

        for di, _data in enumerate(data):
            req = dut.drivers[di].req._ag
            wIn = dut.drivers[di].w._ag
            dataIt = iter(_data)

            addr = dataAddress[di]
            end = False
            while True:
                frameSize = self._rand.getrandbits(4) + 1
                frame = []
                try:
                    for _ in range(frameSize):
                        frame.append(next(dataIt))
                except StopIteration:
                    end = True

                if frame:
                    req.data.append(mkReq(addr, len(frame) - 1))
                    wIn.data.extend([(d, _mask, i == len(frame) - 1)
                                     for i, d in enumerate(frame)])
                    addr += len(frame) * dut.DATA_WIDTH // 8
                if end:
                    break

        ra = self.randomize
        for d in dut.drivers:
            ra(d.req)
            ra(d.w)
            ra(d.ack)

        ra(dut.wDatapump.req)
        ra(dut.wDatapump.w)
        ra(dut.wDatapump.ack)

        self.runSim(self.DRIVER_CNT * N * 50 * Time.ns)
        for i, baseAddr in enumerate(dataAddress):
            inMem = m.getArray(baseAddr, dut.DATA_WIDTH // 8, N)
            self.assertValSequenceEqual(inMem, data[i], f"driver:{i:d}")


if __name__ == "__main__":
    _ALL_TCs = [WStrictOrderInterconnectTC, WStrictOrderInterconnect2TC]
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([WStrictOrderInterconnectTC("test_randomized2")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
