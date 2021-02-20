#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from hwt.pyUtils.arrayQuery import flatten
from hwt.serializer.combLoopAnalyzer import CombLoopAnalyzer
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import allValuesToInts
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.lsu.read_aggregator import AxiReadAggregator
from hwtLib.amba.axi_comp.sim.ram import AxiSimRam
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.examples.errors.combLoops import freeze_set_of_sets
from hwtSimApi.constants import CLK_PERIOD


class AxiReadAggregator_1word_burst_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = u = AxiReadAggregator()
        u.ID_WIDTH = 2
        u.CACHE_LINE_SIZE = 4
        u.DATA_WIDTH = 4 * 8
        cls.ID_CNT = 2 ** u.ID_WIDTH
        cls.WORD_SIZE = u.DATA_WIDTH // 8
        cls.compileSim(u)

    def test_no_comb_loops(self):
        s = CombLoopAnalyzer()
        s.visit_Unit(self.u)
        comb_loops = freeze_set_of_sets(s.report())
        # for loop in comb_loops:
        #     print(10 * "-")
        #     for s in loop:
        #         print(s.resolve()[1:])

        self.assertEqual(comb_loops, frozenset())

    def randomize_all(self):
        axi_randomize_per_channel(self, self.u.m)
        axi_randomize_per_channel(self, self.u.s)

    def test_nop(self, randomized=False):
        if randomized:
            self.randomize_all()

        self.runSim(10 * CLK_PERIOD)
        u = self.u
        self.assertEmpty(u.m.ar._ag.data)
        self.assertEmpty(u.s.r._ag.data)

    def test_nop_randomized(self):
        self.test_nop(randomized=True)

    def _test_read(self, id_addr_tuples, randomize=False, REF_DATA=0x1000, time_multiplier=2):
        u = self.u
        mem = AxiSimRam(u.m)
        WORD_SIZE = self.WORD_SIZE
        trans_len = ceil(u.CACHE_LINE_SIZE / WORD_SIZE)

        for trans_id, addr in id_addr_tuples:
            for i in range(trans_len):
                mem.data[addr // WORD_SIZE + i] = addr + i + REF_DATA
            trans = u.s._ag.create_addr_req(addr, trans_len - 1, _id=trans_id)
            u.s.ar._ag.data.append(trans)

        t = ceil((len(id_addr_tuples) * trans_len + 10) * time_multiplier * CLK_PERIOD )
        if randomize:
            self.randomize_all()
            t *= 3

        self.runSim(t)

        ref_data = sorted(flatten([
            [(_id, addr + i + REF_DATA, RESP_OKAY, int(i == trans_len - 1))
              for i in range(trans_len)]
            for _id, addr in id_addr_tuples],
            level=1))
        data = sorted(allValuesToInts(u.s.r._ag.data))
        # print("")
        # print(ref_data)
        # print(data)
        self.assertSequenceEqual(data, ref_data)

    def _test_read_from_random_addr(self, address_cnt, N, randomize=False):
        available_addresses = [i * self.u.CACHE_LINE_SIZE for i in range(address_cnt)]
        rand = self._rand
        d_addr_tuples = [(x % self.ID_CNT, rand.choice(available_addresses)) for x in range(N)]
        self._test_read(d_addr_tuples, randomize)

    def _test_read_from_random_addr_and_id(self, id_cnt: int, address_cnt: int, N: int, randomize=False, time_multiplier=1):
        assert id_cnt <= self.ID_CNT
        available_addresses = [i * self.u.CACHE_LINE_SIZE for i in range(address_cnt)]
        available_ids = [i for i in range(id_cnt)]
        rand = self._rand
        d_addr_tuples = [(rand.choice(available_ids), rand.choice(available_addresses)) for _ in range(N)]
        self._test_read(d_addr_tuples, randomize=randomize, time_multiplier=time_multiplier)

    def test_read_from_same_addr_32x(self, randomize=False):
        d_addr_tuples = [(x % self.ID_CNT, 0x0) for x in range(32)]
        self._test_read(d_addr_tuples, randomize)

    def test_r_read_from_same_addr_32x(self, randomize=True):
        self.test_read_from_same_addr_32x(randomize)

    def test_read_1x(self, randomize=False):
        IDS = [(0, 0x0)]
        self._test_read(IDS, randomize)

    def test_r_read_1x(self, randomize=True):
        self.test_read_1x(randomize)

    def test_read_from_sequential_addr_2x(self, randomize=False):
        d_addr_tuples = [(x % self.ID_CNT, x * self.u.CACHE_LINE_SIZE) for x in range(2)]
        self._test_read(d_addr_tuples, randomize)

    def test_r_read_from_sequential_addr_2x(self, randomize=True):
        self.test_read_from_sequential_addr_2x(randomize)

    def test_read_from_random_addr_10x_from_2addresses(self, randomize=False):
        self._test_read_from_random_addr(2, 10, randomize)

    def test_r_read_from_random_addr_10x_from_2addresses(self, randomize=True):
        self.test_read_from_random_addr_10x_from_2addresses(randomize)

    def test_read_from_random_addr_100x_from_10addresses(self, randomize=False):
        self._test_read_from_random_addr(10, 100, randomize)

    def test_r_read_from_random_addr_100x_from_10addresses(self, randomize=True):
        self.test_read_from_random_addr_100x_from_10addresses(randomize)

    def test_read_from_random_addr_100x_from_10addresses_4ids(self, randomize=False):
        self._test_read_from_random_addr_and_id(4, 10, 100, randomize, time_multiplier=3)

    def test_r_read_from_random_addr_100x_from_10addresses_4ids(self, randomize=True):
        self.test_read_from_random_addr_100x_from_10addresses_4ids(randomize)

    def test_read_from_random_addr_100x_from_5addresses_1id(self, randomize=False):
        self._test_read_from_random_addr_and_id(1, 5, 100, randomize, time_multiplier=4)

    def test_r_read_from_random_addr_100x_from_5addresses_1id(self, randomize=True):
        self.test_read_from_random_addr_100x_from_5addresses_1id(randomize)


class AxiReadAggregator_2word_burst_TC(AxiReadAggregator_1word_burst_TC):

    @classmethod
    def setUpClass(cls):
        cls.u = u = AxiReadAggregator()
        u.ID_WIDTH = 2
        u.CACHE_LINE_SIZE = 8
        u.DATA_WIDTH = 4 * 8
        cls.ID_CNT = 2 ** u.ID_WIDTH
        cls.WORD_SIZE = u.DATA_WIDTH // 8
        cls.compileSim(u)


AxiReadAggregator_TCs = [
    AxiReadAggregator_1word_burst_TC,
    AxiReadAggregator_2word_burst_TC
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    #suite.addTest(AxiReadAggregator_1word_burst_TC('test_read_from_random_addr_100x_from_5addresses_1id'))
    for tc in AxiReadAggregator_TCs:
        suite.addTest(unittest.makeSuite(tc))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
