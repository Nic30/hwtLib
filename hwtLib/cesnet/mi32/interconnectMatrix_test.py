#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import READ, WRITE, Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.busInterconnect import AUTO_ADDR, ALL
from hwtLib.cesnet.mi32.interconnectMatrix import Mi32InterconnectMatrix
from pyMathBitPrecise.bit_utils import mask
from hwtLib.cesnet.mi32.sim_ram import Mi32SimRam


class Mi32InterconnectMatrixTC(SimTestCase):
    CLK = 10 * Time.ns

    def mySetUp(self):
        SimTestCase.setUp(self)

        AUTO = AUTO_ADDR

        u = Mi32InterconnectMatrix()
        u.MASTERS = (ALL, )
        u.SLAVES = (
            (0x0000, 0x0100),
            (0x0100, 0x0100),
            (AUTO,   0x0100),
            (AUTO,   0x1000),
        )
        self.DW = 32
        self.wordSize = self.DW // 8
        u.DATA_WIDTH = self.DW
        u.ADDR_WIDTH = u.getOptimalAddrSize()
        self.m = mask(self.wordSize)
        self.u = u
        self.compileSimAndStart(u)

    def test_readAndWrite(self, N=2):
        self.mySetUp()
        u = self.u
        offsets = [0x0, 0x100, 0x200, 0x1000]
        for s, o in zip(u._slaves, offsets):
            self.assertEqual(s[0], o)

        m = self.u.s[0]._ag
        mems = [Mi32SimRam(s) for s in self.u.m]
        MAGIC_R = 10
        MAGIC_W = 100

        expected = []
        expected_r = []
        _mask = self.m
        for si, (mem, offset) in enumerate(zip(mems, offsets)):
            d = {}
            for i in range(N):
                d[i] = mem.data[i] = MAGIC_R + i + si * N
                expected_r.append(d[i])
                m.requests.append((READ, i * 4 + offset))

                w_a = (i + N) * 4 + offset
                w_d = MAGIC_W + i + si * N
                m.requests.append((WRITE, w_a, w_d, _mask))
                d[(w_a - offset) // self.wordSize] = w_d

            expected.append(d)

        self.runSim((10 + 4 * len(offsets) * N) * self.CLK)

        for i, (e, mem) in enumerate(zip(expected, mems)):
            d = {k: int(v) for k, v in mem.data.items()}
            self.assertDictEqual(d, e, i)
        self.assertValSequenceEqual(m.r_data, expected_r)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(Mi32InterconnectMatrixTC('test_read_lat1'))
    suite.addTest(unittest.makeSuite(Mi32InterconnectMatrixTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
