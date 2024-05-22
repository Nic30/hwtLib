#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.utils import addClkRstn
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axiLite_comp.to_axi import AxiLite_to_Axi
from hwtLib.amba.axi_comp.sim.ram import Axi4SimRam
from hwtLib.amba.constants import PROT_DEFAULT, RESP_OKAY
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class AxiLite_to_Axi_withClk(AxiLite_to_Axi):
    @override
    def hwDeclr(self):
        AxiLite_to_Axi.hwDeclr(self)
        addClkRstn(self)


class AxiLite_to_Axi_TC(SimTestCase):
    TRANSACTION_CNT = 32

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = AxiLite_to_Axi_withClk()
        cls.compileSim(cls.dut)

    def randomize_all(self):
        for i in [self.dut.m, self.dut.s]:
            axi_randomize_per_channel(self, i)

    def test_nop(self):
        self.randomize_all()
        self.runSim(10 * CLK_PERIOD)
        m, s = self.dut.s, self.dut.m
        self.assertEmpty(m.r._ag.data)
        self.assertEmpty(m.b._ag.data)
        self.assertEmpty(s.ar._ag.data)
        self.assertEmpty(s.aw._ag.data)
        self.assertEmpty(s.w._ag.data)

    def addr_trans(self, word_i):
        dut = self.dut
        addr = word_i * dut.DATA_WIDTH // 8
        return (addr, PROT_DEFAULT)

    def w_trans(self, data):
        strb = mask(self.dut.DATA_WIDTH // 8)
        return (data, strb)

    def test_read(self):
        N = self.TRANSACTION_CNT
        dut = self.dut

        m = Axi4SimRam(dut.m)

        expected_data = []
        allocated_wods = list(range(N))
        self._rand.shuffle(allocated_wods)
        for word_i in allocated_wods:
            rand_data = self._rand.getrandbits(dut.DATA_WIDTH)
            a_t = self.addr_trans(word_i)
            m.data[word_i] = rand_data
            dut.s.ar._ag.data.append(a_t)
            expected_data.append((rand_data, RESP_OKAY))

        self.runSim(N * 3 * CLK_PERIOD)

        self.assertValSequenceEqual(
            dut.s.r._ag.data,
            expected_data
        )

    def test_write(self):
        N = self.TRANSACTION_CNT
        dut = self.dut

        m = Axi4SimRam(dut.m)

        expected_data = []
        allocated_wods = list(range(N))
        self._rand.shuffle(allocated_wods)
        for word_i in allocated_wods:
            rand_data = self._rand.getrandbits(dut.DATA_WIDTH)

            a_t = self.addr_trans(word_i)
            dut.s.aw._ag.data.append(a_t)

            w_t = self.w_trans(rand_data)
            dut.s.w._ag.data.append(w_t)

            expected_data.append((word_i, rand_data))

        self.runSim(N * 3 * CLK_PERIOD)

        for word_i, expected in expected_data:
            d = m.data.get(word_i, None)
            self.assertValEqual(d, expected)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AxiLite_to_Axi_TC("test_read")])
    suite = testLoader.loadTestsFromTestCase(AxiLite_to_Axi_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
