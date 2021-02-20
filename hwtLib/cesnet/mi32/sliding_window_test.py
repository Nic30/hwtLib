#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import READ, WRITE
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.cesnet.mi32.sim_ram import Mi32SimRam
from hwtLib.cesnet.mi32.sliding_window import Mi32SlidingWindow
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class Mi32SlidingWindowTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = Mi32SlidingWindow()
        u.M_ADDR_WIDTH = 12
        u.WINDOW_SIZE = int(2 ** 10)
        u.ADDR_WIDTH = 11
        cls.compileSim(u)

    def test_read_offset_default(self, MAGIC=99, N=3):
        u = self.u
        addr_req = [(READ, 0x4 * i) for i in range(N)]
        u.s._ag.requests.extend(addr_req)
        m = Mi32SimRam(u.m)
        expected = []
        for i in range(N):
            d = m.data[i] = MAGIC + i + 1
            expected.append(d)

        self.runSim((10 + N) * CLK_PERIOD)
        self.assertValSequenceEqual(u.s._ag.r_data, expected)

    def test_write_offset_default(self, MAGIC=99, N=3):
        u = self.u
        m = mask(u.DATA_WIDTH // 8)
        addr_req = [(WRITE, 0x4 * i, MAGIC + i + 1, m) for i in range(N)]
        expected = [x[2] for x in addr_req]
        u.s._ag.requests.extend(addr_req)
        m = Mi32SimRam(u.m)

        self.runSim((10 + N) * CLK_PERIOD)
        data = m.getArray(0x0, u.DATA_WIDTH // 8, N)
        self.assertValSequenceEqual(data, expected)

    def test_write_with_offset(self, offset=128, MAGIC=99, N=3):
        u = self.u
        m = mask(u.DATA_WIDTH // 8)
        addr_req = [(WRITE, u.WINDOW_SIZE, offset, m),
                    *((WRITE, 0x4 * i, MAGIC + i + 1, m) for i in range(N))]
        expected = [x[2] for x in addr_req[1:]]
        u.s._ag.requests.extend(addr_req)
        m = Mi32SimRam(u.m)

        self.runSim((10 + N) * CLK_PERIOD)
        data = m.getArray(offset, u.DATA_WIDTH // 8, N)
        self.assertValSequenceEqual(data, expected)

    def test_read_with_offset(self, offset=128, MAGIC=99, N=3):
        u = self.u
        m = mask(u.DATA_WIDTH // 8)
        addr_req = [(WRITE, u.WINDOW_SIZE, offset, m),
                    *((READ, 0x4 * i) for i in range(N))]
        u.s._ag.requests.extend(addr_req)
        m = Mi32SimRam(u.m)

        expected = []
        word_offset = (offset // (u.DATA_WIDTH // 8))
        for i in range(N):
            d = m.data[word_offset + i] = MAGIC + i + 1
            expected.append(d)

        self.runSim((10 + N) * CLK_PERIOD)
        data = m.getArray(offset, u.DATA_WIDTH // 8, N)
        self.assertValSequenceEqual(data, expected)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    #suite.addTest(Mi32SlidingWindowTC('test_write_with_offset'))
    suite.addTest(unittest.makeSuite(Mi32SlidingWindowTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
