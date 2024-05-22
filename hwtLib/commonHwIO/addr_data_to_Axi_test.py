#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from hwt.pyUtils.arrayQuery import grouper
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.sim.ram import Axi4SimRam
from hwtLib.commonHwIO.addr_data_to_Axi import AddrDataRdVld_to_Axi
from hwtLib.tools.debug_bus_monitor_ctl import select_bit_range
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class HwIOAddrDataRdVld_to_Axi_1_to_1_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = AddrDataRdVld_to_Axi()
        dut.ADDR_WIDTH = 16 + 2
        dut.S_ADDR_WIDTH = 16
        # in each axi word there is only lower half used
        dut.DATA_WIDTH = dut.S_DATA_WIDTH = dut.S_ADDR_STEP = 32
        dut.M_ADDR_OFFSET = 0
        cls.compileSim(dut)

    def pack_words(self, words, word_width, new_word_width):
        if word_width < new_word_width:
            assert new_word_width % word_width == 0
            word_pack_factor = new_word_width // word_width
            m = mask(new_word_width)
            new_words = []
            for frame_data_words in grouper(word_pack_factor, words):
                f = 0
                for d in reversed(frame_data_words):
                    f <<= word_width
                    f |= d
                new_words.append(f & m)
            return new_words
        elif word_width > new_word_width:
            assert word_width % new_word_width == 0
            word_unpack_factor = word_width // new_word_width
            new_words = []
            for w in words:
                # for i in range(word_unpack_factor-1, -1, -1):
                for i in range(word_unpack_factor):
                    new_words.append(select_bit_range(w, i * new_word_width, new_word_width))

            return new_words
        else:
            return words

    def test_nop(self):
        dut = self.dut

        self.runSim(20 * CLK_PERIOD)
        s_r = dut.s_r
        axi = dut.m

        self.assertEmpty(axi.aw._ag.data)
        self.assertEmpty(axi.w._ag.data)
        self.assertEmpty(axi.ar._ag.data)
        self.assertEmpty(s_r.data._ag.data)

    def test_write(self, N=20, randomize=False):
        dut = self.dut
        s_w = dut.s_w
        axi = dut.m

        m = Axi4SimRam(axi=axi)
        M_DW = axi.DATA_WIDTH
        FRAME_WORD_CNT = ceil((dut.S_ADDR_STEP) / M_DW)
        w_data = [i  # self._rand.getrandbits(M_DW)
                  for i in range(N * FRAME_WORD_CNT)]
        # create data words for P4AppPort
        wr_data = self.pack_words(w_data, M_DW, s_w.DATA_WIDTH)

        for addr, frame in enumerate(wr_data):
            s_w._ag.data.append((addr, frame))

        if randomize:
            axi_randomize_per_channel(self, axi)

        self.runSim(N * FRAME_WORD_CNT * 10 * CLK_PERIOD)

        w_m = mask(s_w.DATA_WIDTH) if s_w.DATA_WIDTH < axi.DATA_WIDTH else mask(axi.DATA_WIDTH)
        addr = dut.M_ADDR_OFFSET
        inMem = m.getArray(addr, M_DW // 8, FRAME_WORD_CNT * N)
        inMem = [None if v is None else v & w_m for v in inMem]
        self.assertValSequenceEqual(inMem, w_data)

    def test_write_randomized(self, N=20):
        self.test_write(N, randomize=True)

    def test_read(self, N=10, randomize=False):
        dut = self.dut
        s_r = dut.s_r
        axi = dut.m

        m = Axi4SimRam(axi=axi)
        M_DW = axi.DATA_WIDTH
        FRAME_WORD_CNT = ceil(dut.S_ADDR_STEP / M_DW)
        r_data = [i  # self._rand.getrandbits(M_DW)
                  for i in range(N * FRAME_WORD_CNT)]
        # create data words for P4AppPort
        rd_data = self.pack_words(r_data, M_DW, s_r.DATA_WIDTH)
        for index, d in enumerate(r_data):
            index = (dut.M_ADDR_OFFSET * 8 // M_DW) + index
            m.data[index] = d

        for addr, _ in enumerate(rd_data):
            s_r.addr._ag.data.append(addr)

        if randomize:
            axi_randomize_per_channel(self, axi)

        self.runSim(N * FRAME_WORD_CNT * 12 * CLK_PERIOD)

        readed = s_r.data._ag.data
        self.assertEqual(len(readed), len(rd_data))
        for addr, (d_ref, d) in enumerate(zip(rd_data, readed)):
            self.assertValEqual(d, d_ref, addr)

    def test_read_randomized(self, N=10):
        self.test_read(N, randomize=True)


class HwIOAddrDataRdVld_to_Axi_1_to_2_TC(HwIOAddrDataRdVld_to_Axi_1_to_1_TC):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = AddrDataRdVld_to_Axi()
        dut.ADDR_WIDTH = 32
        dut.S_ADDR_WIDTH = 16
        # in each axi word there is only lower half used
        dut.DATA_WIDTH = 32
        dut.S_DATA_WIDTH = dut.S_ADDR_STEP = 64
        dut.M_ADDR_OFFSET = 0
        cls.compileSim(dut)


class HwIOAddrDataRdVld_to_Axi_2_to_1_TC(HwIOAddrDataRdVld_to_Axi_1_to_1_TC):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = AddrDataRdVld_to_Axi()
        dut.S_ADDR_WIDTH = 16 - 1
        dut.ADDR_WIDTH = 16
        # in each axi word there is only lower half used
        dut.DATA_WIDTH = 32
        dut.S_DATA_WIDTH = dut.S_ADDR_STEP = 16
        dut.M_ADDR_OFFSET = 0
        cls.compileSim(dut)

HwIOAddrDataRdVld_to_Axi_TCs = [
    HwIOAddrDataRdVld_to_Axi_1_to_1_TC,
    HwIOAddrDataRdVld_to_Axi_1_to_2_TC,
    HwIOAddrDataRdVld_to_Axi_2_to_1_TC,
]

if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HwIOAddrDataRdVld_to_Axi_TC("test_read")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in HwIOAddrDataRdVld_to_Axi_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
