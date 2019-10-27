#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import READ, WRITE, Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.busInterconnect import ACCESS_RW, AUTO_ADDR
from hwtLib.ipif.interconnectMatrix import IpifInterconnectMatrix
from pyMathBitPrecise.bit_utils import mask


class IpifInterconnectMatrixTC(SimTestCase):
    CLK = 10 * Time.ns

    def mySetUp(self, read_latency=0, write_latency=0):
        SimTestCase.setUp(self)

        RW = ACCESS_RW
        AUTO = AUTO_ADDR

        u = IpifInterconnectMatrix(
            masters=[(0x0, RW)],
            slaves=[
                (0x0000, 0x0100, RW),
                (0x0100, 0x0100, RW),
                (AUTO,   0x0100, RW),
                (AUTO,   0x1000, RW),
            ]
        )
        self.DW = 32
        self.wordSize = self.DW // 8
        u.DATA_WIDTH = self.DW
        u.ADDR_WIDTH = u.getOptimalAddrSize()
        self.m = mask(self.wordSize)
        self.u = u
        self.compileSimAndStart(u)
        for s in u.m:
            s._ag.READ_LATENCY = read_latency
            s._ag.WRITE_LATENCY = write_latency

    def test_readAndWrite(self, read_latency=0, write_latency=0, N=2):
        self.mySetUp(read_latency=read_latency,
                     write_latency=write_latency)
        u = self.u
        offsets = [0x0, 0x100, 0x200, 0x1000]
        for s, o in zip(u._slaves, offsets):
            self.assertEqual(s[0], o)

        m = self.u.s[0]._ag
        s = [_s._ag for _s in self.u.m]
        MAGIC_R = 10
        MAGIC_W = 100

        expected = []
        for si, (_s, offset) in enumerate(zip(s, offsets)):
            d = {}
            for i in range(N):
                d[i] = _s.mem[i] = MAGIC_R + i + si * N
                m.requests.append((READ, i * 4 + offset))
                w_a = (i + N) * 4 + offset
                w_d = MAGIC_W + i + si * N
                m.requests.append((WRITE, w_a, w_d, self.m))
                d[(w_a - offset) // self.wordSize] = w_d
            expected.append(d)

        self.runSim((10 + 4 * len(offsets) * N) *
                    (max(read_latency, write_latency) + 1) * self.CLK)

        for i, (e, s) in enumerate(zip(expected, s)):
            d = {k: int(v) for k, v in s.mem.items()}
            self.assertDictEqual(d, e, i)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(IpifInterconnectMatrixTC('test_read_lat1'))
    suite.addTest(unittest.makeSuite(IpifInterconnectMatrixTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
