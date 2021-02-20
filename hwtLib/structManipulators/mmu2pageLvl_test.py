#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import WRITE, NOP
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.datapump.sim_ram import AxiDpSimRam
from hwtLib.structManipulators.mmu_2pageLvl import MMU_2pageLvl
from pyMathBitPrecise.bit_utils import mask
from hwtSimApi.constants import CLK_PERIOD


class MMU_2pageLvl_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = MMU_2pageLvl()
        cls.compileSim(cls.u)

    def buildVirtAddr(self, lvl1pgtIndx, lvl2pgtIndx, pageOffset):
        u = self.u
        return (
            (lvl1pgtIndx << (u.LVL2_PAGE_TABLE_INDX_WIDTH + u.PAGE_OFFSET_WIDTH))
            | (lvl2pgtIndx << u.PAGE_OFFSET_WIDTH) | pageOffset
        )

    def test_nop(self):
        u = self.u

        self.runSim(10 * CLK_PERIOD)

        self.assertEmpty(u.rDatapump.req._ag.data)
        self.assertEmpty(u.physOut._ag.data)
        self.assertValEqual(u.segfault._ag.data[-1], 0)

    def test_lvl1_fault(self):
        u = self.u
        for i in range(u.LVL1_PAGE_TABLE_ITEMS):
            u.lvl1Table._ag.requests.append((WRITE, i, mask(32)))

        u.virtIn._ag.data.extend(
            [NOP
             for _ in range(u.LVL1_PAGE_TABLE_ITEMS + 5)]
            + [0, ])

        self.runSim((u.LVL1_PAGE_TABLE_ITEMS + 20) * CLK_PERIOD)
        self.assertEmpty(u.physOut._ag.data)
        self.assertValEqual(u.segfault._ag.data[-1], 1)

    def test_lvl2_fault(self):
        u = self.u
        MAGIC = 45

        m = AxiDpSimRam(u.DATA_WIDTH, u.clk, rDatapumpIntf=u.rDatapump)

        addr_bytes = u.ADDR_WIDTH // 8
        ADDR_INVALID = mask(u.ADDR_WIDTH)
        lvl2pgt = m.calloc(
            u.LVL2_PAGE_TABLE_ITEMS, addr_bytes,
            initValues=[ADDR_INVALID for _ in range(u.LVL2_PAGE_TABLE_ITEMS)])

        u.lvl1Table._ag.requests.append((WRITE, MAGIC, lvl2pgt))

        va = self.buildVirtAddr(MAGIC, 0, 0)
        # wait for lvl1Table storage init
        u.virtIn._ag.data.extend([NOP, NOP, va])

        self.runSim(10 * CLK_PERIOD)

        self.assertEmpty(u.physOut._ag.data)
        self.assertValEqual(u.segfault._ag.data[-1], 1)

    def test_translate10xRandomized(self):
        u = self.u
        N = 10
        # self.randomize(u.rDatapump.req)
        self.randomize(u.rDatapump.r)
        self.randomize(u.virtIn)
        self.randomize(u.physOut)

        m = AxiDpSimRam(u.DATA_WIDTH, u.clk, rDatapumpIntf=u.rDatapump)
        virt = u.virtIn._ag.data
        virt.extend([NOP for _ in range(N)])

        expected = []
        ADDR_INVALID = mask(u.ADDR_WIDTH)
        for i in range(N):
            lvl2pgtData = [int(2 ** 12) * i2 if i + 1 == i2 else ADDR_INVALID
                           for i2 in range(u.LVL2_PAGE_TABLE_ITEMS)]
            lvl2pgt = m.calloc(u.LVL2_PAGE_TABLE_ITEMS,
                               u.ADDR_WIDTH // 8,
                               initValues=lvl2pgtData)

            u.lvl1Table._ag.requests.append((WRITE, i, lvl2pgt))
            v = self.buildVirtAddr(i, i + 1, i + 1)
            virt.append(v)
            expected.append(int(2 ** 12) * (i + 1) + i + 1)

        self.runSim(N * 30 * CLK_PERIOD)

        self.assertValSequenceEqual(u.physOut._ag.data, expected)
        self.assertValEqual(u.segfault._ag.data[-1], 0)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(MMU_2pageLvl_TC('test_translate10xRandomized'))
    suite.addTest(unittest.makeSuite(MMU_2pageLvl_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
