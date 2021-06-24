#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import WRITE, READ
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi_comp.to_axiLite_test import Axi_to_AxiLite_TC
from hwtLib.avalon.mm import AvalonMmAgent
from hwtLib.avalon.mm_buff import AvalonMmBuff
from hwtLib.avalon.sim.ram import AvalonMmSimRam
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class AvalonMmBuff_TC(SimTestCase):
    TRANSACTION_CNT = 1
    MAX_LEN = 4

    @classmethod
    def setUpClass(cls):
        u = cls.u = AvalonMmBuff()
        u.MAX_BURST = cls.MAX_LEN
        u.DATA_WIDTH = 64
        u.ADDR_BUFF_DEPTH = 4
        u.DATA_BUFF_DEPTH = 4

        cls.compileSim(u)

    def randomize_all(self):
        pass

    def test_nop(self):
        self.randomize_all()
        self.runSim(10 * CLK_PERIOD)

        s = self.u.s._ag
        m = AvalonMmSimRam(self.u.m)
        self.assertEmpty(s.rDataAg.data)
        self.assertEmpty(s.wRespAg.data)
        self.assertDictEqual(m.data, {})

    def test_read(self):
        N = 0
        u = self.u
        self.randomize_all()
        mem = AvalonMmSimRam(u.m)
        expected_data = []
        addr = 0
        memory_init = []
        avmm: AvalonMmAgent = u.s._ag
        for _ in range(self.TRANSACTION_CNT):
            len_ = 1 + Axi_to_AxiLite_TC.get_rand_in_range(self, self.MAX_LEN - 1)
            N += len_ + 1 + 1
            rand_data = [self._rand.getrandbits(u.DATA_WIDTH)
                         for _ in range(len_)]
            # rand_data = [i + 1 for i in range(len_)]
            memory_init.extend(rand_data)
            # print(f"0x{addr:x}, {len_:d}", rand_data)
            a_t = (READ, addr, len_, None, None)
            avmm.addrAg.data.append(a_t)
            expected_data.extend(rand_data)
            addr += len(rand_data) * u.DATA_WIDTH // 8

        mem.data = {i: v for i, v in enumerate(memory_init)}

        self.runSim(N * 3 * CLK_PERIOD)
        self.assertValSequenceEqual(avmm.rData, [(d, None) for d in expected_data])

    def test_write(self):
        N = self.TRANSACTION_CNT
        u = self.u

        mem = AvalonMmSimRam(u.m)
        avmm: AvalonMmAgent = u.s._ag
        # avmm.addrAg._debugOutput = sys.stdout
        expected_data = []
        addr = 0
        m = mask(u.DATA_WIDTH // 8)
        for _ in range(self.TRANSACTION_CNT):
            len_ = 1 + Axi_to_AxiLite_TC.get_rand_in_range(self, self.MAX_LEN - 1)

            N += len_ + 3
            rand_data = [self._rand.getrandbits(u.DATA_WIDTH)
                        for _ in range(len_)]

            word_i = addr // (u.DATA_WIDTH // 8)
            rand_data = [word_i + i + 1 for i in range(len_)]
            # print(f"0x{addr:x}, {len_:d}", rand_data)
            for i, d in enumerate(rand_data):
                a_t = (WRITE, addr, len_, d, m)
                avmm.addrAg.data.append(a_t)

                expected_data.append((word_i + i, d))
            addr += len(rand_data) * u.DATA_WIDTH // 8

        self.runSim(N * 3 * CLK_PERIOD)

        for word_i, expected in expected_data:
            d = mem.data.get(word_i, None)
            self.assertValEqual(d, expected, ("word ", word_i))


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(AvalonMmBuff_TC('test_write'))
    suite.addTest(unittest.makeSuite(AvalonMmBuff_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
