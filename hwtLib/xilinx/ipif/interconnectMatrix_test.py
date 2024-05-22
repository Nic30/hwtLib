#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import READ, WRITE, Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.busInterconnect import AUTO_ADDR, ALL
from hwtLib.xilinx.ipif.interconnectMatrix import IpifInterconnectMatrix
from pyMathBitPrecise.bit_utils import mask


class IpifInterconnectMatrixTC(SimTestCase):
    CLK = 10 * Time.ns

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def mySetUp(self, read_latency=0, write_latency=0):
        SimTestCase.setUp(self)

        AUTO = AUTO_ADDR

        dut = IpifInterconnectMatrix()
        dut.MASTERS = (ALL,)
        dut.SLAVES = (
            (0x0000, 0x0100),
            (0x0100, 0x0100),
            (AUTO, 0x0100),
            (AUTO, 0x1000),
        )
        self.DW = 32
        self.wordSize = self.DW // 8
        dut.DATA_WIDTH = self.DW
        dut.ADDR_WIDTH = dut.getOptimalAddrSize()
        self.m = mask(self.wordSize)
        self.dut = dut
        self.compileSimAndStart(dut)
        for s in dut.m:
            s._ag.READ_LATENCY = read_latency
            s._ag.WRITE_LATENCY = write_latency
        
        return dut
        
    def test_readAndWrite(self, read_latency=0, write_latency=0, N=2):
        dut = self.mySetUp(read_latency=read_latency,
                           write_latency=write_latency)
        offsets = [0x0, 0x100, 0x200, 0x1000]
        for s, o in zip(dut._slaves, offsets):
            self.assertEqual(s[0], o)

        m = self.dut.s[0]._ag
        s = [_s._ag for _s in self.dut.m]
        MAGIC_R = 10
        MAGIC_W = 100

        expected = []
        expected_r = []
        for si, (_s, offset) in enumerate(zip(s, offsets)):
            d = {}
            for i in range(N):
                d[i] = _s.mem[i] = MAGIC_R + i + si * N
                expected_r.append(d[i])
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
        self.assertValSequenceEqual(m.r_data, expected_r)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([IpifInterconnectMatrixTC("test_read_lat1")])
    suite = testLoader.loadTestsFromTestCase(IpifInterconnectMatrixTC)

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
