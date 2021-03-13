#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.lsu.write_aggregator import AxiWriteAggregator
from hwtLib.amba.axi_comp.sim.ram import AxiSimRam
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask, set_bit_range, int_list_to_int, \
    get_bit_range


class AxiWriteAggregator_1word_per_cachelineTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = u = AxiWriteAggregator()
        u.ADDR_WIDTH = 16
        u.ID_WIDTH = 2
        u.CACHE_LINE_SIZE = 4
        u.DATA_WIDTH = 32
        u.MAX_BLOCK_DATA_WIDTH = 8
        cls.compileSim(u)

    def randomize_all(self):
        self.randomize(self.u.w)
        axi_randomize_per_channel(self, self.u.m)
        # self.randomize(self.u.m.aw)
        # self.randomize(self.u.m.w)
        # self.randomize(self.u.m.b)

    def test_nop(self, randomized=False):
        if randomized:
            self.randomize_all()

        self.runSim(10 * CLK_PERIOD)
        u = self.u
        self.assertEmpty(u.m.aw._ag.data)
        self.assertEmpty(u.m.w._ag.data)

    def test_nop_randomized(self):
        self.test_nop(randomized=True)

    def test_non_mergable_no_ack(self, N=10, randomized=False):
        u = self.u
        u.w._ag.data.extend((i, 10 + i, mask(u.CACHE_LINE_SIZE))
                            for i in range(N))
        if randomized:
            self.randomize_all()

        self.runSim((N + 10) * 2 * CLK_PERIOD * u.BUS_WORDS_IN_CACHE_LINE)

        SIZE = 2 ** u.ID_WIDTH
        aw = u.m.aw._ag
        self.assertValSequenceEqual(aw.data, [
            aw.create_addr_req(addr=u.CACHE_LINE_SIZE * i,
                               _len=u.BUS_WORDS_IN_CACHE_LINE - 1,
                               _id=i)
            for i in range(min(SIZE, N))
        ])

        w_ref = []
        for i in range(min(SIZE, N)):
            for last, w_i in iter_with_last(range(u.BUS_WORDS_IN_CACHE_LINE)):
                d = (10 + i if w_i == 0 else 0,
                     mask(u.DATA_WIDTH // 8), int(last))
                w_ref.append(d)
        # for i, (x0, x1) in enumerate(zip(u.m.w._ag.data, w_ref)):
        #    print(i, allValuesToInts(x0), x1)

        self.assertValSequenceEqual(u.m.w._ag.data, w_ref)

        # 1 item is currently handled by agent, 1 item in tmp reg
        self.assertEqual(len(u.w._ag.data), N - SIZE - 1 - 1)

    def test_non_mergable_no_ack_randomized(self, N=10):
        self.test_non_mergable_no_ack(N, randomized=True)

    def test_single_write(self):
        u = self.u
        d = int_list_to_int(range(u.CACHE_LINE_SIZE), 8)
        u.w._ag.data.append((1, d, mask(u.CACHE_LINE_SIZE)))
        self.runSim(10 * CLK_PERIOD)

        aw = u.m.aw._ag
        self.assertValSequenceEqual(aw.data, [
            aw.create_addr_req(addr=1 * u.CACHE_LINE_SIZE,
                               _len=u.BUS_WORDS_IN_CACHE_LINE - 1,
                               _id=0),
        ])
        self.assertValSequenceEqual(u.m.w._ag.data, [
            (get_bit_range(d, u.DATA_WIDTH * i, u.DATA_WIDTH),
             mask(u.DATA_WIDTH // 8), int(last))
            for last, i in iter_with_last(range(u.BUS_WORDS_IN_CACHE_LINE))
        ])

    def test_with_mem(self, N=10, randomized=False):
        u = self.u
        mem = AxiSimRam(u.m)
        u.w._ag.data.extend((i, 10 + i, mask(u.CACHE_LINE_SIZE))
                            for i in range(N))
        if randomized:
            self.randomize_all()

        self.runSim((N + 10) * 3 * CLK_PERIOD * u.BUS_WORDS_IN_CACHE_LINE)
        mem_val = mem.getArray(0, u.CACHE_LINE_SIZE, N)
        self.assertValSequenceEqual(mem_val, [10 + i for i in range(N)])

    def test_with_mem_randomized(self, N=10):
        self.test_with_mem(N=N, randomized=True)

    def test_mergable(self, N=10, ADDRESSES=[0, ], randomized=False):
        u = self.u
        mem = AxiSimRam(u.m)
        expected = {}
        for a in ADDRESSES:
            for i in range(N):
                B_i = i % (u.CACHE_LINE_SIZE)
                d = i << (B_i * 8)
                m = 1 << B_i
                u.w._ag.data.append((a, d, m))
                v = expected.get(a, 0)
                v = set_bit_range(v, B_i * 8, 8, i)
                expected[a] = v

        t = (N * len(ADDRESSES) + 10) * 3 * \
            u.BUS_WORDS_IN_CACHE_LINE * CLK_PERIOD
        if randomized:
            #t *= 2
            self.randomize_all()

        self.runSim(t)
        data = mem.getArray(0, u.CACHE_LINE_SIZE, max(ADDRESSES) + 1)
        for a in ADDRESSES:
            self.assertValEqual(
                data[a], expected[a],
                "%d: expected 0x%08x got 0x%08x, 0x%08x" %
                (a, expected[a], data[a].val, data[a].vld_mask))

    def test_mergable2(self, N=10, ADDRESSES=[0, ], randomized=False):
        """
        same as test_mergable just the inner cycle is reversed
        """
        u = self.u
        mem = AxiSimRam(u.m)
        expected = {}
        for i in range(N):
            offset = i * N
            for a in ADDRESSES:
                B_i = (i % 4)
                _i = ((offset + i) % 0xff)
                d = _i << (B_i * 8)
                m = 1 << B_i
                u.w._ag.data.append((a, d, m))
                v = expected.get(a, 0)
                v = set_bit_range(v, B_i * 8, 8, _i)
                expected[a] = v

        if randomized:
            self.randomize_all()

        self.runSim((N * len(ADDRESSES) + 10) * 3 *
                    u.BUS_WORDS_IN_CACHE_LINE * CLK_PERIOD)
        for a in ADDRESSES:
            self.assertValEqual(
                mem.data[a], expected[a], "%d: 0x%08x" % (a, expected[a]))

    def test_mergable_4_address(self, N=10, ADDRESSES=[1, 2, 3, 4], randomized=False):
        self.test_mergable(N, ADDRESSES, randomized)

    def test_mergable_randomized(self, N=10, ADDRESSES=[0, ]):
        self.test_mergable(N, ADDRESSES, randomized=True)

    def test_mergable_4_address_randomized(self, N=10, ADDRESSES=[1, 2, 3, 4]):
        self.test_mergable(N, ADDRESSES, randomized=True)


class AxiWriteAggregator_2words_per_cachelineTC(AxiWriteAggregator_1word_per_cachelineTC):

    @classmethod
    def setUpClass(cls):
        cls.u = u = AxiWriteAggregator()
        u.ADDR_WIDTH = 16
        u.ID_WIDTH = 2
        u.CACHE_LINE_SIZE = 8
        u.DATA_WIDTH = 32
        u.MAX_BLOCK_DATA_WIDTH = 8
        cls.compileSim(u)


AxiWriteAggregator_TCs = [
    AxiWriteAggregator_1word_per_cachelineTC,
    AxiWriteAggregator_2words_per_cachelineTC,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(AxiWriteAggregator_2words_per_cachelineTC('test_mergable'))
    # suite.addTest(AxiWriteAggregator_1word_per_cachelineTC('test_mergable'))

    suite.addTest(unittest.makeSuite(AxiWriteAggregator_1word_per_cachelineTC))
    suite.addTest(unittest.makeSuite(AxiWriteAggregator_2words_per_cachelineTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
