#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.bits import HBits
from hwt.pyUtils.arrayQuery import grouper
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.sim.ram import Axi4LiteSimRam
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.resize import AxiResize
from hwtLib.amba.constants import PROT_DEFAULT
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class AxiResizeTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = dut = AxiResize(Axi4Lite)
        dut.DATA_WIDTH = 32
        dut.OUT_DATA_WIDTH = 512
        cls.compileSim(dut)

    def randomize_all(self):
        axi_randomize_per_channel(self, self.dut.m)
        axi_randomize_per_channel(self, self.dut.s)

    def test_read_radomized(self, n=4 * (512 // 32), n2=2, magic=99, randomize=True):
        self.test_read(n, n2, magic, randomize)

    def test_read(self, n=4 * (512 // 32), n2=2, magic=99, randomize=False):
        dut = self.dut
        in_addr_step = dut.DATA_WIDTH // 8
        out_addr_step = dut.OUT_DATA_WIDTH // 8
        in_words_in_out_word = out_addr_step // in_addr_step
        expected = []
        for _ in range(n2):
            for in_i in range(n):
                dut.s.ar._ag.data.append((in_i * in_addr_step, PROT_DEFAULT))
                in_w = magic + in_i
                expected.append(in_w)

        m = Axi4LiteSimRam(dut.m)
        in_t = HBits(dut.DATA_WIDTH)[in_words_in_out_word]
        out_t = HBits(dut.OUT_DATA_WIDTH)
        for out_w_i, out_w in enumerate(grouper(in_words_in_out_word, expected, padvalue=0)):
            w = in_t.from_py(out_w)._reinterpret_cast(out_t)
            m.data[out_w_i] = w

        t = n2 * n
        if randomize:
            self.randomize_all()
            t *= 5

        self.runSim((t + 10) * CLK_PERIOD)
        self.assertValSequenceEqual(dut.s.r._ag.data, [(v, 0) for v in expected])

    def test_write_randomized(self, n=4 * (512 // 32), n2=2, magic=99, randomize=True):
        self.test_write(n, n2, magic, randomize)

    def test_write(self, n=4 * (512 // 32), n2=2, magic=99, randomize=False):
        dut = self.dut
        in_addr_step = dut.DATA_WIDTH // 8
        out_addr_step = dut.OUT_DATA_WIDTH // 8
        in_words_in_out_word = out_addr_step // in_addr_step
        w_data = []
        for _ in range(n2):
            for in_i in range(n):
                dut.s.aw._ag.data.append((in_i * in_addr_step, PROT_DEFAULT))
                in_w = magic + in_i
                w_data.append(in_w)
        dut.s.w._ag.data.extend([(d, mask(in_addr_step)) for d in w_data])

        m = Axi4LiteSimRam(dut.m)

        in_t = HBits(dut.DATA_WIDTH)[n]
        out_t = HBits(dut.OUT_DATA_WIDTH)[n // in_words_in_out_word]

        t = n2 * n
        if randomize:
            self.randomize_all()
            t *= 5

        self.runSim((t + 10) * CLK_PERIOD)
        v = m.getArray(0x0, out_addr_step, n // in_words_in_out_word)
        v = out_t.from_py(v)._reinterpret_cast(in_t)

        self.assertValSequenceEqual(v, w_data[n * (n2 - 1):])


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AxiResizeTC("test_write")])
    suite = testLoader.loadTestsFromTestCase(AxiResizeTC)

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
