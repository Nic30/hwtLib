#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

from hwt.code import Concat
from hwt.hdl.types.arrayVal import HArrayVal
from hwt.hdl.types.bits import Bits
from hwt.serializer.combLoopAnalyzer import CombLoopAnalyzer
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.cache.caheWriteAllocWawOnlyWritePropagating import AxiCaheWriteAllocWawOnlyWritePropagating
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.examples.errors.combLoops import freeze_set_of_sets
from hwtLib.tools.debug_bus_monitor_ctl import select_bit_range
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import set_bit_range, mask


class AxiCaheWriteAllocWawOnlyWritePropagatingTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = u = AxiCaheWriteAllocWawOnlyWritePropagating()
        u.DATA_WIDTH = 32
        u.CACHE_LINE_SIZE = 4
        u.CACHE_LINE_CNT = 16
        u.MAX_BLOCK_DATA_WIDTH = 8
        u.WAY_CNT = 2
        cls.ADDR_STEP = u.DATA_WIDTH // 8
        cls.WAY_CACHELINES = u.CACHE_LINE_CNT // u.WAY_CNT
        return u

    def setUp(self):
        SingleUnitSimTestCase.setUp(self)
        m = self.rtl_simulator.model
        u = self.u
        self.TAGS = [
            getattr(m.tag_array_inst.tag_mem_inst, f"children_{i:d}_inst").io.ram_memory
            for i in range(u.tag_array.tag_record_t.bit_length() * u.WAY_CNT // 8)
        ]
        self.DATA = [
            getattr(m.data_array_inst, f"children_{i:d}_inst").io.ram_memory
            for i in range(u.CACHE_LINE_SIZE)
        ]

    def _clean_mems(self, mems):
        for mem in mems:
            mem.val = mem.def_val = mem._dtype.from_py([0 for _ in range(mem._dtype.size)])

    def clean_tags(self):
        self._clean_mems(self.TAGS)

    def clean_data(self):
        self._clean_mems(self.DATA)

    def set_data(self, index, way, data):
        u = self.u
        WAY_CACHELINES = u.CACHE_LINE_CNT // u.WAY_CNT
        i = way * WAY_CACHELINES + index
        self._set_to_mems(self.DATA, i, data)

    @staticmethod
    def _get_from_mems(mems: List[HArrayVal], i: int):
        res = [data_mem.val[i] for data_mem in reversed(mems)]
        return Concat(*res)

    @staticmethod
    def _set_to_mems(mems: List[HArrayVal], i: int, val: int):
        for B_i, data_mem  in enumerate(mems):
            _data = select_bit_range(val, B_i * 8, 8)
            data_mem.val[i] = data_mem.def_val[i] = data_mem._dtype.element_t.from_py(_data)

    def get_data(self, index, way):
        i = way * self.WAY_CACHELINES + index
        return self._get_from_mems(self.DATA, i)

    def set_tag(self, addr, way):
        u = self.u
        tag, index, offset = u.parse_addr_int(addr)
        assert offset == 0, addr
        tag_t = u.tag_array.tag_record_t
        tag_t_w = tag_t.bit_length()
        v = tag_t.from_py({"tag": tag, "valid": 1})._reinterpret_cast(Bits(tag_t_w))

        cur_v = self._get_from_mems(self.TAGS, index)
        assert cur_v._is_full_valid(), (cur_v, index)
        val = set_bit_range(cur_v.val, way * tag_t_w, tag_t_w, v.val)
        self._set_to_mems(self.TAGS, index, val)

        return index

    def cacheline_insert(self, addr, way, data):
        index = self.set_tag(addr, way)
        self.set_data(index, way, data)

    def get_cachelines(self):
        u = self.u
        res = {}
        tags_t = u.tag_array.tag_record_t[u.WAY_CNT]
        tags_raw_t = Bits(tags_t.bit_length())
        for index in range(2 ** u.INDEX_W):
            tags = self._get_from_mems(self.TAGS, index)
            tags = tags_raw_t.from_py(tags.val, tags.vld_mask)._reinterpret_cast(tags_t)
            for way, t in enumerate(tags):
                if t.valid:
                    data = self.get_data(index, way)
                    addr = u.deparse_addr(t.tag, index, 0)
                    if data._is_full_valid():
                        data = int(data)
                    res[int(addr)] = data
        return res

    def randomize_all(self):
        u = self.u
        axi_randomize_per_channel(self, u.s)
        axi_randomize_per_channel(self, u.m)

    def test_utils(self):
        self.clean_tags()
        self.clean_data()
        self.assertDictEqual(self.get_cachelines(), {})

        expected = {}
        MAGIC = 99
        for w in range(self.u.WAY_CNT):
            a = (w * self.WAY_CACHELINES + 3) * self.ADDR_STEP
            self.cacheline_insert(a, w, MAGIC + w)
            expected[a] = MAGIC + w
            self.assertDictEqual(self.get_cachelines(), expected)

    def test_no_comb_loops(self):
        s = CombLoopAnalyzer()
        s.visit_Unit(self.u)
        comb_loops = freeze_set_of_sets(s.report())
        # for loop in comb_loops:
        #     print(10 * "-")
        #     for s in loop:
        #         print(s.resolve()[1:])

        self.assertEqual(comb_loops, frozenset())

    def test_nop(self):
        u = self.u
        self.randomize_all()
        self.runSim(50 * CLK_PERIOD)
        for x in [u.m.ar, u.m.aw, u.m.w, u.s.r, u.s.b]:
            self.assertEmpty(x._ag.data)

    def test_read_through(self, N=10, randomized=False):
        # Every transaction should be checked if present in cache, should not be found and should
        # be forwarded on axi "m" port
        u = self.u
        self.clean_tags()
        ref = [
            u.s.ar._ag.create_addr_req(addr=i * self.ADDR_STEP, _len=0, _id=i)
            for i in range(N)
        ]
        u.s.ar._ag.data.extend(ref)
        t = (N + 5) * CLK_PERIOD
        if randomized:
            self.randomize_all()
            t *= 3

        self.runSim(t)
        self.assertValSequenceEqual(u.m.ar._ag.data, ref)
        for x in [u.m.aw, u.m.w, u.s.r, u.s.b]:
            self.assertEmpty(x._ag.data)

    def test_read_from_everywhere(self, N_PER_WAY=10, MAGIC=99, randomized=False):
        # Every transaction should be read from the cache
        u = self.u
        self.clean_tags()
        self.clean_data()
        ID_MAX = 2 ** u.ID_WIDTH
        WAY_CACHELINES = self.WAY_CACHELINES
        expected_r = []
        for w in range(u.WAY_CNT):
            for i in range(N_PER_WAY):
                i = i % WAY_CACHELINES
                addr = (i + w * WAY_CACHELINES) * self.ADDR_STEP
                d = w * MAGIC + i
                _id = i % ID_MAX
                self.cacheline_insert(addr, w, d)
                req = u.s.ar._ag.create_addr_req(addr=addr, _len=0, _id=_id)
                u.s.ar._ag.data.append(req)
                expected_r.append((_id, d, RESP_OKAY, 1))

        t = (5 + u.WAY_CNT * N_PER_WAY) * CLK_PERIOD
        if randomized:
            self.randomize_all()
            t *= 3
        self.runSim(t)
        for x in [u.s.ar, u.m.ar, u.m.aw, u.m.w, u.s.b]:
            self.assertEmpty(x._ag.data, x)

        self.assertValSequenceEqual(u.s.r._ag.data, expected_r)

    def test_read_from_everywhere_r(self, N_PER_WAY=50, MAGIC=99):
        self.test_read_from_everywhere(
            N_PER_WAY=N_PER_WAY,
            MAGIC=MAGIC,
            randomized=True)

    def _test_write_to(self, N_PER_WAY=8, MAGIC=99, preallocate=False, randomized=False):
        # Every cacheline should be stored in cache as there is plenty of space
        u = self.u
        self.clean_tags()
        self.clean_data()

        WAY_CACHELINES = self.WAY_CACHELINES
        ID_MAX = 2 ** u.ID_WIDTH
        aw = u.s.aw._ag
        expected = {}
        b_expected = []
        M = mask(u.CACHE_LINE_SIZE)
        for w in range(u.WAY_CNT):
            for i in range(N_PER_WAY):
                i = i % WAY_CACHELINES
                addr = (i + w * WAY_CACHELINES) * self.ADDR_STEP
                d = w * MAGIC + i
                expected[addr] = d
                if preallocate:
                    self.cacheline_insert(addr, w, 0)

                _id = i % ID_MAX
                req = aw.create_addr_req(addr=addr, _len=0, _id=_id)
                aw.data.append(req)
                u.s.w._ag.data.append((d, M, 1))
                b_expected.append((_id, RESP_OKAY))
        if preallocate:
            self.assertDictEqual(self.get_cachelines(), {k: 0 for k in expected.keys()})
        t = (u.WAY_CNT * N_PER_WAY + 10) * CLK_PERIOD
        if randomized:
            t *= 3
            self.randomize_all()

        self.runSim(t)
        for x in [u.s.aw, u.s.r, u.m.ar, u.m.aw, u.m.w]:
            self.assertEmpty(x._ag.data, x)

        self.assertDictEqual(self.get_cachelines(), expected)
        self.assertValSequenceEqual(u.s.b._ag.data, b_expected)

    def test_write_to_empty(self, N_PER_WAY=8, MAGIC=99, preallocate=False, randomized=False):
        self._test_write_to(N_PER_WAY, MAGIC, preallocate, randomized)

    def test_write_to_preallocated(self, N_PER_WAY=8, MAGIC=99):
        self._test_write_to(N_PER_WAY=N_PER_WAY, MAGIC=MAGIC, preallocate=True)

    def test_write_to_empty_r(self, N_PER_WAY=50, MAGIC=99):
        self._test_write_to(N_PER_WAY=N_PER_WAY, MAGIC=MAGIC, preallocate=False, randomized=True)

    def test_write_to_preallocated_r(self, N_PER_WAY=50, MAGIC=99):
        self._test_write_to(N_PER_WAY=N_PER_WAY, MAGIC=MAGIC, preallocate=True, randomized=True)

    # write victim flush


AxiCaheWriteAllocWawOnlyWritePropagatingTCs = [
    AxiCaheWriteAllocWawOnlyWritePropagatingTC,

]


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    #suite.addTest(AxiCaheWriteAllocWawOnlyWritePropagatingTC('test_write_to_empty_r'))
    suite.addTest(unittest.makeSuite(AxiCaheWriteAllocWawOnlyWritePropagatingTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)