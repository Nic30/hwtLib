#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.operators.indexing import (SimpleIndexingSplit,
                                               SimpleIndexingJoin,
                                               SimpleIndexingRangeJoin,
                                               IndexingInernSplit,
                                               IndexingInernJoin,
                                               IndexingInernRangeSplit)


class IndexingTC(SimTestCase):
    def setUpUnit(self, unit):
        self.prepareUnit(unit)

    def test_split(self):
        u = SimpleIndexingSplit()
        self.setUpUnit(u)
        u.a._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])

        self.doSim(80 * Time.ns)

        self.assertSequenceEqual([0, 1, 0, 1, None, 1, 0, 1], agInts(u.b))
        self.assertSequenceEqual([0, 0, 1, 1, None, 1, 1, 0], agInts(u.c))

    def test_join(self):
        u = SimpleIndexingJoin()
        self.setUpUnit(u)

        u.b._ag.data.extend([0, 1, 0, 1, None, 1, 0, 1])
        u.c._ag.data.extend([0, 0, 1, 1, None, 1, 1, 0])

        self.doSim(80 * Time.ns)

        self.assertSequenceEqual([0, 1, 2, 3, None, 3, 2, 1], agInts(u.a))

    def test_rangeJoin(self):
        u = SimpleIndexingRangeJoin()
        self.setUpUnit(u)

        u.b._ag.data.extend([0, 3, 0, 3, None, 3, 0, 3])
        u.c._ag.data.extend([0, 0, 3, 3, None, 3, 3, 0])

        self.doSim(80 * Time.ns)

        self.assertSequenceEqual([0, 3, 12, 15, None, 15, 12, 3], agInts(u.a))

    def test_internSplit(self):
        u = IndexingInernSplit()
        self.setUpUnit(u)

        u.a._ag.data.extend([0, 1, 2, 3, None, 3, 0, 3])

        self.doSim(80 * Time.ns)

        self.assertSequenceEqual([0, 1, 2, 3, None, 3, 0, 3], agInts(u.b))

    def test_internJoin(self):
        u = IndexingInernJoin()
        self.setUpUnit(u)

        u.a._ag.data.extend([0, 1, 0, 1, None, 0, 1, 0])
        u.b._ag.data.extend([0, 0, 1, 1, None, 0, 1, 0])

        self.doSim(80 * Time.ns)

        self.assertSequenceEqual([0, 1, 0, 1, None, 0, 1, 0], agInts(u.c))
        self.assertSequenceEqual([0, 0, 1, 1, None, 0, 1, 0], agInts(u.d))

    def test_indexingInernRangeSplit(self):
        u = IndexingInernRangeSplit()
        self.setUpUnit(u)
        reference = list(range(2 ** 4)) + [None, ]
        u.a._ag.data.extend(reference)

        self.doSim((2 ** 4 + 2) * 10 * Time.ns)

        self.assertSequenceEqual(reference, agInts(u.b))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(IndexingTC('test_split'))
    suite.addTest(unittest.makeSuite(IndexingTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
