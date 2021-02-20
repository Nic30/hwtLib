#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.bits import Bits
from hwt.pyUtils.arrayQuery import grouper
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.sim.ram import Axi4LiteSimRam
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.resize import AxiResize
from hwtLib.amba.constants import PROT_DEFAULT
from pyMathBitPrecise.bit_utils import mask
from hwtSimApi.constants import CLK_PERIOD


class AxiResizeTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = u = AxiResize(Axi4Lite)
        u.DATA_WIDTH = 32
        u.OUT_DATA_WIDTH = 512
        cls.compileSim(u)

    def randomize_all(self):
        axi_randomize_per_channel(self, self.u.m)
        axi_randomize_per_channel(self, self.u.s)

    def test_read_radomized(self, n=4 * (512 // 32), n2=2, magic=99, randomize=True):
        self.test_read(n, n2, magic, randomize)

    def test_read(self, n=4 * (512 // 32), n2=2, magic=99, randomize=False):
        u = self.u
        in_addr_step = u.DATA_WIDTH // 8
        out_addr_step = u.OUT_DATA_WIDTH // 8
        in_words_in_out_word = out_addr_step // in_addr_step
        expected = []
        for _ in range(n2):
            for in_i in range(n):
                u.s.ar._ag.data.append((in_i * in_addr_step, PROT_DEFAULT))
                in_w = magic + in_i
                expected.append(in_w)

        m = Axi4LiteSimRam(u.m)
        in_t = Bits(u.DATA_WIDTH)[in_words_in_out_word]
        out_t = Bits(u.OUT_DATA_WIDTH)
        for out_w_i, out_w in enumerate(grouper(in_words_in_out_word, expected, padvalue=0)):
            w = in_t.from_py(out_w)._reinterpret_cast(out_t)
            m.data[out_w_i] = w

        t = n2 * n
        if randomize:
            self.randomize_all()
            t *= 5

        self.runSim((t + 10) * CLK_PERIOD)
        self.assertValSequenceEqual(u.s.r._ag.data, [(v, 0) for v in expected])

    def test_write_randomized(self, n=4 * (512 // 32), n2=2, magic=99, randomize=True):
        self.test_write(n, n2, magic, randomize)

    def test_write(self, n=4 * (512 // 32), n2=2, magic=99, randomize=False):
        u = self.u
        in_addr_step = u.DATA_WIDTH // 8
        out_addr_step = u.OUT_DATA_WIDTH // 8
        in_words_in_out_word = out_addr_step // in_addr_step
        w_data = []
        for _ in range(n2):
            for in_i in range(n):
                u.s.aw._ag.data.append((in_i * in_addr_step, PROT_DEFAULT))
                in_w = magic + in_i
                w_data.append(in_w)
        u.s.w._ag.data.extend([(d, mask(in_addr_step)) for d in w_data])

        m = Axi4LiteSimRam(u.m)

        in_t = Bits(u.DATA_WIDTH)[n]
        out_t = Bits(u.OUT_DATA_WIDTH)[n // in_words_in_out_word]

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
    suite = unittest.TestSuite()

    # suite.addTest(Mi32AgentTC('test_write'))
    suite.addTest(unittest.makeSuite(AxiResizeTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
