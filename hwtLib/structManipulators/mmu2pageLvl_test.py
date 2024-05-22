#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import WRITE, NOP
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.datapump.sim_ram import AxiDpSimRam
from hwtLib.structManipulators.mmu_2pageLvl import MMU_2pageLvl
from pyMathBitPrecise.bit_utils import mask
from hwtSimApi.constants import CLK_PERIOD


class MMU_2pageLvl_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = MMU_2pageLvl()
        cls.compileSim(cls.dut)

    def buildVirtAddr(self, lvl1pgtIndx, lvl2pgtIndx, pageOffset):
        dut = self.dut
        return (
            (lvl1pgtIndx << (dut.LVL2_PAGE_TABLE_INDX_WIDTH + dut.PAGE_OFFSET_WIDTH))
            | (lvl2pgtIndx << dut.PAGE_OFFSET_WIDTH) | pageOffset
        )

    def test_nop(self):
        dut = self.dut

        self.runSim(10 * CLK_PERIOD)

        self.assertEmpty(dut.rDatapump.req._ag.data)
        self.assertEmpty(dut.physOut._ag.data)
        self.assertValEqual(dut.segfault._ag.data[-1], 0)

    def test_lvl1_fault(self):
        dut = self.dut
        for i in range(dut.LVL1_PAGE_TABLE_ITEMS):
            dut.lvl1Table._ag.requests.append((WRITE, i, mask(32)))

        dut.virtIn._ag.data.extend(
            [NOP
             for _ in range(dut.LVL1_PAGE_TABLE_ITEMS + 5)]
            + [0, ])

        self.runSim((dut.LVL1_PAGE_TABLE_ITEMS + 20) * CLK_PERIOD)
        self.assertEmpty(dut.physOut._ag.data)
        self.assertValEqual(dut.segfault._ag.data[-1], 1)

    def test_lvl2_fault(self):
        dut = self.dut
        MAGIC = 45

        m = AxiDpSimRam(dut.DATA_WIDTH, dut.clk, rDatapumpHwIO=dut.rDatapump)

        addr_bytes = dut.ADDR_WIDTH // 8
        ADDR_INVALID = mask(dut.ADDR_WIDTH)
        lvl2pgt = m.calloc(
            dut.LVL2_PAGE_TABLE_ITEMS, addr_bytes,
            initValues=[ADDR_INVALID for _ in range(dut.LVL2_PAGE_TABLE_ITEMS)])

        dut.lvl1Table._ag.requests.append((WRITE, MAGIC, lvl2pgt))

        va = self.buildVirtAddr(MAGIC, 0, 0)
        # wait for lvl1Table storage init
        dut.virtIn._ag.data.extend([NOP, NOP, va])

        self.runSim(10 * CLK_PERIOD)

        self.assertEmpty(dut.physOut._ag.data)
        self.assertValEqual(dut.segfault._ag.data[-1], 1)

    def test_translate10xRandomized(self):
        dut = self.dut
        N = 10
        # self.randomize(dut.rDatapump.req)
        self.randomize(dut.rDatapump.r)
        self.randomize(dut.virtIn)
        self.randomize(dut.physOut)

        m = AxiDpSimRam(dut.DATA_WIDTH, dut.clk, rDatapumpHwIO=dut.rDatapump)
        virt = dut.virtIn._ag.data
        virt.extend([NOP for _ in range(N)])

        expected = []
        ADDR_INVALID = mask(dut.ADDR_WIDTH)
        for i in range(N):
            lvl2pgtData = [int(2 ** 12) * i2 if i + 1 == i2 else ADDR_INVALID
                           for i2 in range(dut.LVL2_PAGE_TABLE_ITEMS)]
            lvl2pgt = m.calloc(dut.LVL2_PAGE_TABLE_ITEMS,
                               dut.ADDR_WIDTH // 8,
                               initValues=lvl2pgtData)

            dut.lvl1Table._ag.requests.append((WRITE, i, lvl2pgt))
            v = self.buildVirtAddr(i, i + 1, i + 1)
            virt.append(v)
            expected.append(int(2 ** 12) * (i + 1) + i + 1)

        self.runSim(N * 30 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.physOut._ag.data, expected)
        self.assertValEqual(dut.segfault._ag.data[-1], 0)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([MMU_2pageLvl_TC("test_translate10xRandomized")])
    suite = testLoader.loadTestsFromTestCase(MMU_2pageLvl_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
