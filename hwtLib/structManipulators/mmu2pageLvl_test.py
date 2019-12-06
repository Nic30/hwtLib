#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import WRITE, NOP
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.abstract.denseMemory import DenseMemory
from hwtLib.structManipulators.mmu_2pageLvl import MMU_2pageLvl
from pycocotb.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class MMU_2pageLvl_TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = u = MMU_2pageLvl()
        cls.DATA_WIDTH = int(u.DATA_WIDTH)
        return cls.u

    def setUp(self):
        super(MMU_2pageLvl_TC, self).setUp()
        self.LVL2_PAGE_TABLE_ITEMS = int(self.u.LVL2_PAGE_TABLE_ITEMS)
        self.LVL1_PAGE_TABLE_ITEMS = int(self.u.LVL1_PAGE_TABLE_ITEMS)

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
        for i in range(self.LVL1_PAGE_TABLE_ITEMS):
            u.lvl1Table._ag.requests.append((WRITE, i, mask(32)))

        u.virtIn._ag.data.extend(
            [NOP
             for _ in range(self.LVL1_PAGE_TABLE_ITEMS + 5)]
            + [0, ])

        self.runSim((self.LVL1_PAGE_TABLE_ITEMS + 20) * CLK_PERIOD)
        self.assertEmpty(u.physOut._ag.data)
        self.assertValEqual(u.segfault._ag.data[-1], 1)

    def test_lvl2_fault(self):
        u = self.u
        MAGIC = 45

        m = DenseMemory(self.DATA_WIDTH, u.clk, rDatapumpIntf=u.rDatapump)

        lvl2pgt = m.calloc(
            self.LVL2_PAGE_TABLE_ITEMS, 4,
            initValues=[-1 for _ in range(self.LVL2_PAGE_TABLE_ITEMS)])

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

        m = DenseMemory(self.DATA_WIDTH, u.clk, rDatapumpIntf=u.rDatapump)
        virt = u.virtIn._ag.data
        virt.extend([NOP for _ in range(N)])

        expected = []
        for i in range(N):
            lvl2pgtData = [int(2 ** 12) * i2 if i + 1 == i2 else -1
                           for i2 in range(self.LVL2_PAGE_TABLE_ITEMS)]
            lvl2pgt = m.calloc(self.LVL2_PAGE_TABLE_ITEMS,
                               4,
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
