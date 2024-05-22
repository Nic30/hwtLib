#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import WRITE, READ
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.avalon.axiToMm import Axi4_to_AvalonMm
from hwtLib.avalon.sim.ram import AvalonMmSimRam
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class AxiToAvalonMm_len0_prioW_TC(SimTestCase):
    R_SIZE_FIFO_DEPTH = 4
    R_DATA_FIFO_DEPTH = 4
    RW_PRIORITY = WRITE
    MAX_LEN = 0

    @classmethod
    def setUpClass(cls):
        super(AxiToAvalonMm_len0_prioW_TC, cls).setUpClass()
        dut = cls.dut = Axi4_to_AvalonMm()
        dut.R_SIZE_FIFO_DEPTH = cls.R_SIZE_FIFO_DEPTH
        dut.R_DATA_FIFO_DEPTH = cls.R_DATA_FIFO_DEPTH
        dut.RW_PRIORITY = cls.RW_PRIORITY
        cls.compileSim(dut)

    def randomize_all(self):
        dut = self.dut
        axi_randomize_per_channel(self, dut.s)

    def test_nop(self):
        self.runSim(10 * CLK_PERIOD)

    def test_read(self, N=10, randomize=False):
        dut = self.dut
        ADDR_STEP = dut.DATA_WIDTH // 8
        MAX_LEN = self.MAX_LEN
        MAX_SIZE = MAX_LEN + 1
        m = AvalonMmSimRam(dut.m)
        for i in range(0, N * MAX_SIZE, MAX_SIZE):
            dut.s.ar._ag.data.append(dut.s._ag.create_addr_req(i * ADDR_STEP, MAX_LEN))
            for i2 in range(MAX_SIZE):
                m.data[i + i2] = i + i2

        t = 35 + N * MAX_SIZE
        if randomize:
            self.randomize_all()
            t *= 3

        self.runSim(t * CLK_PERIOD)
        self.assertValSequenceEqual(dut.s.r._ag.data,
                                    [(0, i, RESP_OKAY, int((i + 1) % MAX_SIZE == 0))
                                     for i in range(N * MAX_SIZE)])

    def test_read_r(self, N=10):
        self.test_read(N=N, randomize=True)

    def test_write(self, N=10, randomize=False):
        dut = self.dut
        ADDR_STEP = dut.DATA_WIDTH // 8
        MAX_LEN = self.MAX_LEN
        MAX_SIZE = MAX_LEN + 1

        m = AvalonMmSimRam(dut.m)
        for i in range(0, N * MAX_SIZE, MAX_SIZE):
            dut.s.aw._ag.data.append(dut.s._ag.create_addr_req(i * ADDR_STEP, MAX_LEN))
            for i2 in range(MAX_SIZE):
                dut.s.w._ag.data.append((i + i2, mask(ADDR_STEP), int(i2 == MAX_LEN)))

        t = 10 + N * MAX_SIZE
        if randomize:
            self.randomize_all()
            t *= 6

        self.runSim(t * CLK_PERIOD)
        self.assertValSequenceEqual(
            m.getArray(0, ADDR_STEP, N * MAX_SIZE),
            [i for i in range(N * MAX_SIZE)]
        )
        self.assertValSequenceEqual(
            dut.s.b._ag.data,
            [(0, RESP_OKAY) for _ in range(N)]
        )

    def test_write_r(self, N=10):
        self.test_write(N=N, randomize=True)


class AxiToAvalonMm_len2_prioW_TC(AxiToAvalonMm_len0_prioW_TC):
    MAX_LEN = 2


class AxiToAvalonMm_len0_prioR_TC(AxiToAvalonMm_len0_prioW_TC):
    MAX_LEN = 2
    RW_PRIORITY = READ


class AxiToAvalonMm_len2_prioR_TC(AxiToAvalonMm_len0_prioW_TC):
    MAX_LEN = 2
    RW_PRIORITY = READ


AxiToAvalonMm_TCs = [
    AxiToAvalonMm_len0_prioW_TC,
    AxiToAvalonMm_len2_prioW_TC,
    AxiToAvalonMm_len0_prioR_TC,
    AxiToAvalonMm_len2_prioR_TC
]

if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AxiToAvalonMm_len2_TC("test_write_r")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in AxiToAvalonMm_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
