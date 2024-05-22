#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.datapump.sim_ram import AxiDpSimRam
from hwtLib.structManipulators.arrayItemGetter import ArrayItemGetter
from hwtSimApi.constants import CLK_PERIOD


class ArrayItemGetterTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = ArrayItemGetter()
        dut.ID = 3
        dut.ITEMS = 32
        dut.DATA_WIDTH = 64
        dut.ITEM_WIDTH = 64
        cls.compileSim(dut)

    def test_nop(self):
        dut = self.dut
        self.runSim(20 * CLK_PERIOD)

        self.assertEqual(len(dut.rDatapump.req._ag.data), 0)
        self.assertEqual(len(dut.item._ag.data), 0)

    def test_singleGet(self):
        dut = self.dut
        t = 5
        BASE = 8 * (dut.DATA_WIDTH // 8)
        MAGIC = 99
        INDEX = dut.ITEMS - 1

        dut.base._ag.data.append(BASE)
        dut.index._ag.data.append(INDEX)

        m = AxiDpSimRam(dut.DATA_WIDTH, dut.clk, rDatapumpHwIO=dut.rDatapump)
        m.data[BASE // 8 + INDEX] = MAGIC

        self.runSim(t * CLK_PERIOD)

        self.assertValSequenceEqual(dut.item._ag.data, [MAGIC, ])


class ArrayItemGetter2in1WordTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = ArrayItemGetter()
        dut.ID = 3
        dut.ITEMS = 32
        dut.DATA_WIDTH = 64
        dut.ITEM_WIDTH = 32
        cls.compileSim(dut)

    def test_nop(self):
        dut = self.dut
        self.runSim(20 * CLK_PERIOD)

        self.assertEqual(len(dut.rDatapump.req._ag.data), 0)
        self.assertEqual(len(dut.item._ag.data), 0)

    def test_get(self):
        dut = self.dut
        MAGIC = 99
        N = dut.ITEMS
        t = 10 + N

        m = AxiDpSimRam(dut.DATA_WIDTH, dut.clk, rDatapumpHwIO=dut.rDatapump)
        base = m.calloc(dut.ITEMS,
                        dut.ITEM_WIDTH // 8,
                        initValues=[
                                      MAGIC + i
                                      for i in range(N)
                                      ])
        dut.base._ag.data.append(base)
        dut.index._ag.data.extend([i for i in range(N)])

        self.runSim(t * CLK_PERIOD)

        self.assertValSequenceEqual(dut.item._ag.data,
                                    [
                                      MAGIC + i
                                      for i in range(N)
                                    ])


if __name__ == "__main__":
    _ALL_TCs = [ArrayItemGetterTC, ArrayItemGetter2in1WordTC]
    testLoader = unittest.TestLoader()
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
