#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdlConvertorAst.to.hdlUtils import iter_with_last
from hwtLib.amba.axi_comp.lsu.store_queue_write_propagating import AxiStoreQueueWritePropagating
from hwtLib.amba.axi_comp.lsu.write_aggregator_test import AxiWriteAggregator_1word_per_cachelineTC
from hwtLib.amba.axi_comp.sim.ram import AxiSimRam
from hwtLib.amba.constants import RESP_EXOKAY, RESP_OKAY
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class AxiStoreQueueWritePropagating_1word_per_cachelineTC(AxiWriteAggregator_1word_per_cachelineTC):
    SPEC_R_LATENCY = 3
    ADDR_STEP = 4

    @classmethod
    def setUpClass(cls):
        cls.u = u = AxiStoreQueueWritePropagating()
        u.ADDR_WIDTH = 16
        u.ID_WIDTH = 2
        u.CACHE_LINE_SIZE = 4
        u.DATA_WIDTH = 32
        u.MAX_BLOCK_DATA_WIDTH = 8
        cls.compileSim(u)

    def randomize_all(self):
        AxiWriteAggregator_1word_per_cachelineTC.randomize_all(self)
        self.randomize(self.u.speculative_read_addr)
        self.randomize(self.u.speculative_read_data)

    def test_spec_read_non_existing(self, N=10, randomize=False):
        u = self.u
        ref = []
        for i in range(N):
            u.speculative_read_addr._ag.data.append((i % 4, i * self.ADDR_STEP))
            ref.append((i % 4, None, RESP_EXOKAY, 1))

        t = CLK_PERIOD * (N + 5) * 2
        if randomize:
            self.randomize_all()

        self.runSim(t)
        self.assertValSequenceEqual(u.speculative_read_data._ag.data, ref)

    def test_spec_read_non_existing_r(self, N=10):
        self.test_spec_read_non_existing(N, randomize=True)

    def test_spec_read_non_matching(self, N=10, randomize=False):
        u = self.u
        ref = []
        for i in range(N):
            u.speculative_read_addr._ag.data.append((i % 4, (i + N) * self.ADDR_STEP))
            ref.append((i % 4, None, RESP_EXOKAY, 1))

        mem = AxiSimRam(u.m)
        u.w._ag.data.extend((i, 10 + i, mask(u.CACHE_LINE_SIZE))
                            for i in range(N))

        t = (N + 10) * 3 * CLK_PERIOD * u.BUS_WORDS_IN_CACHE_LINE
        if randomize:
            self.randomize_all()

        self.runSim(t)

        self.assertValSequenceEqual(u.speculative_read_data._ag.data, ref)
        mem_val = mem.getArray(0, u.CACHE_LINE_SIZE, N)
        self.assertValSequenceEqual(mem_val, [10 + i for i in range(N)])

    def test_spec_read_in_reg_match(self, N=10, randomize=False):
        u = self.u
        ref = []
        for last, i in iter_with_last(range(N)):
            id_ = i % 4
            u.speculative_read_addr._ag.data.append((id_, 1 * self.ADDR_STEP))
            d = 10 + i
            if not last:
                # because of the latency the data can be writen soner
                # than speculative read finishes
                d += 1

            ref.append((id_, d, RESP_OKAY, 1))

        mem = AxiSimRam(u.m)
        u.w._ag.data.extend((1, 10 + i, mask(u.CACHE_LINE_SIZE))
                            for i in range(N))

        t = (N + 10) * 3 * CLK_PERIOD * u.BUS_WORDS_IN_CACHE_LINE
        if randomize:
            self.randomize_all()

        self.runSim(t)

        self.assertValSequenceEqual(u.speculative_read_data._ag.data, ref)
        mem_val = mem.getArray(0, u.CACHE_LINE_SIZE, N)
        self.assertValSequenceEqual(mem_val, [10 + N - 1 if i == 1 else None for i in range(N)])

    def test_spec_read_in_ram_match(self, N=10, randomize=False):
        u = self.u
        ref = []
        # read from 0 to shift all other reads in time so the addresses
        # the data stored in RAM memory of the sotre buffer
        for i in range(3):
            u.speculative_read_addr._ag.data.append((3, 10 * self.ADDR_STEP))
            ref.append((3, None, RESP_EXOKAY, 1))

        for i in range(N):
            u.speculative_read_addr._ag.data.append((i % 4, i * self.ADDR_STEP))
            ref.append((i % 4, 10 + i, RESP_OKAY, 1))

        mem = AxiSimRam(u.m)
        u.w._ag.data.extend((i, 10 + i, mask(u.CACHE_LINE_SIZE))
                            for i in range(N))

        t = (N + 10) * 3 * CLK_PERIOD * u.BUS_WORDS_IN_CACHE_LINE
        if randomize:
            self.randomize_all()

        self.runSim(t)

        self.assertValSequenceEqual(u.speculative_read_data._ag.data, ref)
        mem_val = mem.getArray(0, u.CACHE_LINE_SIZE, N)
        self.assertValSequenceEqual(mem_val, [10 + i for i in range(N)])

    #def test_spec_read_ramdom(self, N=100):
    #    # ramdomly write and speculatively read and verify that the data
    #    # is latest value of cacheline in the time before latency of speculative read
    #    pass

AxiStoreQueueWritePropagating_TCs = [
    AxiStoreQueueWritePropagating_1word_per_cachelineTC,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(AxiStoreQueueWritePropagating_1word_per_cachelineTC('test_spec_read_in_reg_match'))
    suite.addTest(unittest.makeSuite(AxiStoreQueueWritePropagating_1word_per_cachelineTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
