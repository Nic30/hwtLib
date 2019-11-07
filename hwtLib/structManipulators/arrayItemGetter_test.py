#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SimTestCase, SingleUnitSimTestCase
from hwtLib.abstract.denseMemory import DenseMemory
from hwtLib.structManipulators.arrayItemGetter import ArrayItemGetter
from pycocotb.constants import CLK_PERIOD


class ArrayItemGetterTC(SingleUnitSimTestCase):
    @classmethod
    def getUnit(cls):
        u = cls.u = ArrayItemGetter()
        cls.ID = 3
        u.ID = cls.ID
        u.ITEMS = cls.ITEMS = 32
        u.DATA_WIDTH = cls.DATA_WIDTH = 64
        u.ITEM_WIDTH = cls.ITEM_WIDTH = 64
        return u

    def test_nop(self):
        u = self.u
        self.runSim(20 * CLK_PERIOD)

        self.assertEqual(len(u.rDatapump.req._ag.data), 0)
        self.assertEqual(len(u.item._ag.data), 0)

    def test_singleGet(self):
        u = self.u
        t = 5
        BASE = 8 * (self.DATA_WIDTH // 8)
        MAGIC = 99
        INDEX = self.ITEMS - 1

        u.base._ag.data.append(BASE)
        u.index._ag.data.append(INDEX)

        m = DenseMemory(self.DATA_WIDTH, u.clk, rDatapumpIntf=u.rDatapump)
        m.data[BASE // 8 + INDEX] = MAGIC

        self.runSim(t * CLK_PERIOD)

        self.assertValSequenceEqual(u.item._ag.data, [MAGIC, ])


class ArrayItemGetter2in1WordTC(SingleUnitSimTestCase):
    @classmethod
    def getUnit(cls):
        u = cls.u = ArrayItemGetter()
        cls.ID = u.ID = 3
        u.ITEMS = cls.ITEMS = 32
        u.DATA_WIDTH = cls.DATA_WIDTH = 64
        u.ITEM_WIDTH = cls.ITEM_WIDTH = 32
        return u

    def test_nop(self):
        u = self.u
        self.runSim(20 * CLK_PERIOD)

        self.assertEqual(len(u.rDatapump.req._ag.data), 0)
        self.assertEqual(len(u.item._ag.data), 0)

    def test_get(self):
        u = self.u
        MAGIC = 99
        N = self.ITEMS
        t = 10 + N

        m = DenseMemory(self.DATA_WIDTH, u.clk, rDatapumpIntf=u.rDatapump)
        base = m.calloc(self.ITEMS,
                        self.ITEM_WIDTH // 8,
                        initValues=[
                                      MAGIC + i
                                      for i in range(N)
                                      ])
        u.base._ag.data.append(base)
        u.index._ag.data.extend([i for i in range(N)])

        self.runSim(t * CLK_PERIOD)

        self.assertValSequenceEqual(u.item._ag.data,
                                    [
                                      MAGIC + i
                                      for i in range(N)
                                    ])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(ArrayItemGetter2in1WordTC('test_get'))
    suite.addTest(unittest.makeSuite(ArrayItemGetterTC))
    suite.addTest(unittest.makeSuite(ArrayItemGetter2in1WordTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
