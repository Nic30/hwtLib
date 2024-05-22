#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import READ, WRITE
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.cesnet.mi32.sim_ram import Mi32SimRam
from hwtLib.cesnet.mi32.sliding_window import Mi32SlidingWindow
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class Mi32SlidingWindowTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = Mi32SlidingWindow()
        dut.M_ADDR_WIDTH = 12
        dut.WINDOW_SIZE = int(2 ** 10)
        dut.ADDR_WIDTH = 11
        cls.compileSim(dut)

    def test_read_offset_default(self, MAGIC=99, N=3):
        dut = self.dut
        addr_req = [(READ, 0x4 * i) for i in range(N)]
        dut.s._ag.requests.extend(addr_req)
        m = Mi32SimRam(dut.m)
        expected = []
        for i in range(N):
            d = m.data[i] = MAGIC + i + 1
            expected.append(d)

        self.runSim((10 + N) * CLK_PERIOD)
        self.assertValSequenceEqual(dut.s._ag.r_data, expected)

    def test_write_offset_default(self, MAGIC=99, N=3):
        dut = self.dut
        m = mask(dut.DATA_WIDTH // 8)
        addr_req = [(WRITE, 0x4 * i, MAGIC + i + 1, m) for i in range(N)]
        expected = [x[2] for x in addr_req]
        dut.s._ag.requests.extend(addr_req)
        m = Mi32SimRam(dut.m)

        self.runSim((10 + N) * CLK_PERIOD)
        data = m.getArray(0x0, dut.DATA_WIDTH // 8, N)
        self.assertValSequenceEqual(data, expected)

    def test_write_with_offset(self, offset=128, MAGIC=99, N=3):
        dut = self.dut
        m = mask(dut.DATA_WIDTH // 8)
        addr_req = [(WRITE, dut.WINDOW_SIZE, offset, m),
                    *((WRITE, 0x4 * i, MAGIC + i + 1, m) for i in range(N))]
        expected = [x[2] for x in addr_req[1:]]
        dut.s._ag.requests.extend(addr_req)
        m = Mi32SimRam(dut.m)

        self.runSim((10 + N) * CLK_PERIOD)
        data = m.getArray(offset, dut.DATA_WIDTH // 8, N)
        self.assertValSequenceEqual(data, expected)

    def test_read_with_offset(self, offset=128, MAGIC=99, N=3):
        dut = self.dut
        m = mask(dut.DATA_WIDTH // 8)
        addr_req = [(WRITE, dut.WINDOW_SIZE, offset, m),
                    *((READ, 0x4 * i) for i in range(N))]
        dut.s._ag.requests.extend(addr_req)
        m = Mi32SimRam(dut.m)

        expected = []
        word_offset = (offset // (dut.DATA_WIDTH // 8))
        for i in range(N):
            d = m.data[word_offset + i] = MAGIC + i + 1
            expected.append(d)

        self.runSim((10 + N) * CLK_PERIOD)
        data = m.getArray(offset, dut.DATA_WIDTH // 8, N)
        self.assertValSequenceEqual(data, expected)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Mi32SlidingWindowTC("test_write_with_offset")])
    suite = testLoader.loadTestsFromTestCase(Mi32SlidingWindowTC)

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
