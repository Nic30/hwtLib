#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axi_comp.lsu.store_queue_write_propagating import Axi4StoreQueueWritePropagating
from hwtLib.amba.axi_comp.lsu.write_aggregator_test import AxiWriteAggregator_1word_per_cachelineTC
from hwtLib.amba.axi_comp.sim.ram import Axi4SimRam
from hwtLib.amba.constants import RESP_EXOKAY, RESP_OKAY
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class Axi4StoreQueueWritePropagating_1word_per_cachelineTC(AxiWriteAggregator_1word_per_cachelineTC):
    SPEC_R_LATENCY = 3
    ADDR_STEP = 4

    @classmethod
    def setUpClass(cls):
        cls.dut = m = Axi4StoreQueueWritePropagating()
        m.ADDR_WIDTH = 16
        m.ID_WIDTH = 3
        m.CACHE_LINE_SIZE = 4
        m.DATA_WIDTH = 32
        m.MAX_BLOCK_DATA_WIDTH = 8
        cls.compileSim(m)

    def randomize_all(self):
        AxiWriteAggregator_1word_per_cachelineTC.randomize_all(self)
        self.randomize(self.dut.speculative_read_addr)
        self.randomize(self.dut.speculative_read_data)

    def test_spec_read_non_existing(self, N=10, randomize=False):
        dut = self.dut
        ref = []
        for i in range(N):
            dut.speculative_read_addr._ag.data.append((i % 4, i * self.ADDR_STEP))
            ref.append((i % 4, None, RESP_EXOKAY, 1))

        t = CLK_PERIOD * (N + 6) * 2
        if randomize:
            self.randomize_all()

        self.runSim(t)
        self.assertValSequenceEqual(dut.speculative_read_data._ag.data, ref)

    def test_spec_read_non_existing_r(self, N=10):
        self.test_spec_read_non_existing(N, randomize=True)

    def test_spec_read_non_matching(self, N=10, randomize=False):
        dut = self.dut
        ref = []
        for i in range(N):
            dut.speculative_read_addr._ag.data.append((i % 4, (i + N) * self.ADDR_STEP))
            ref.append((i % 4, None, RESP_EXOKAY, 1))

        mem = Axi4SimRam(dut.m)
        for i in range(N):
            dut.s.aw._ag.data.append(
                dut.s.aw._ag.create_addr_req(addr=i * self.ADDR_STEP, _len=0, _id=0)
            )
            dut.s.w._ag.data.append(
                (10 + i, mask(dut.CACHE_LINE_SIZE), 1))

        t = (N + 10) * 3 * CLK_PERIOD * dut.BUS_WORDS_IN_CACHE_LINE
        if randomize:
            self.randomize_all()

        self.runSim(t)

        self.assertValSequenceEqual(dut.speculative_read_data._ag.data, ref)
        mem_val = mem.getArray(0, dut.CACHE_LINE_SIZE, N)
        self.assertValSequenceEqual(mem_val, [10 + i for i in range(N)])

    def test_spec_read_in_reg_match(self, N=10, randomize=False):
        dut = self.dut
        ref = []
        addr = 1 * self.ADDR_STEP
        ref.append((0, None, RESP_EXOKAY, 1))
        dut.speculative_read_addr._ag.data.append((0, addr))

        for i in range(N):
            id_ = i % 4
            d = 10 + i
            # add write request for next time
            dut.s.aw._ag.data.append(
                    dut.s.aw._ag.create_addr_req(addr=addr, _len=0, _id=0)
                )
            dut.s.w._ag.data.append((d, mask(dut.CACHE_LINE_SIZE), 1))

            if i < N - 2:
                dut.speculative_read_addr._ag.data.append((id_, addr))
                # add speculative read result for later checking
                d += 2  # + latency of the port
                ref.append((id_, d, RESP_OKAY, 1))

        mem = Axi4SimRam(dut.m)
        t = (N + 10) * 3 * CLK_PERIOD * dut.BUS_WORDS_IN_CACHE_LINE
        if randomize:
            self.randomize_all()

        self.runSim(t)

        self.assertValSequenceEqual(dut.speculative_read_data._ag.data, ref)
        mem_val = mem.getArray(0, dut.CACHE_LINE_SIZE, N)
        self.assertValSequenceEqual(mem_val, [10 + N - 1 if i == 1 else None for i in range(N)])

    def test_spec_read_in_ram_match(self, N=10, randomize=False):
        dut = self.dut
        ref = []
        # read from 0 to shift all other reads in time so the addresses
        # the data stored in RAM memory of the sotre buffer
        for i in range(3):
            dut.speculative_read_addr._ag.data.append((3, 10 * self.ADDR_STEP))
            ref.append((3, None, RESP_EXOKAY, 1))
        
        finalData = []
        for i in range(N):
            d = 10 + i
            addr = i * self.ADDR_STEP

            dut.s.aw._ag.data.append(
                dut.s.aw._ag.create_addr_req(addr=addr, _len=0, _id=0)
            )
            dut.s.w._ag.data.append(
                (d, mask(dut.CACHE_LINE_SIZE), 1)
            )
            # this read will hapen after 3 clock delay because of prequel
            dut.speculative_read_addr._ag.data.append((i % 4, addr))
            ref.append((i % 4, d, RESP_OKAY, 1))
            finalData.append(d)

        mem = Axi4SimRam(dut.m)
        t = (N + 10) * 3 * CLK_PERIOD * dut.BUS_WORDS_IN_CACHE_LINE
        if randomize:
            self.randomize_all()

        self.runSim(t)

        self.assertValSequenceEqual(dut.speculative_read_data._ag.data, ref)
        mem_val = mem.getArray(0, dut.CACHE_LINE_SIZE, N)
        self.assertValSequenceEqual(mem_val, finalData)

    # def test_spec_read_ramdom(self, N=100):
    #    # ramdomly write and speculatively read and verify that the data
    #    # is latest value of cacheline in the time before latency of speculative read
    #    pass


Axi4StoreQueueWritePropagating_TCs = [
    Axi4StoreQueueWritePropagating_1word_per_cachelineTC,
]

if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4StoreQueueWritePropagating_1word_per_cachelineTC("test_spec_read_in_ram_match")])
    suite = testLoader.loadTestsFromTestCase(Axi4StoreQueueWritePropagating_1word_per_cachelineTC)

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
