#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.operators.indexing import (
    SimpleIndexingSplit,
    SimpleIndexingJoin,
    SimpleIndexingRangeJoin,
    IndexingInernSplit,
    IndexingInernJoin,
    IndexingInernRangeSplit)


class IndexingTC(SimTestCase):

    def test_split(self):
        u = SimpleIndexingSplit()
        self.compileSimAndStart(u)
        u.a._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])

        self.runSim(80 * Time.ns)

        self.assertValSequenceEqual(u.b._ag.data,
                                    [0, 1, 0, 1, None, 1, 0, 1])
        self.assertValSequenceEqual(u.c._ag.data,
                                    [0, 0, 1, 1, None, 1, 1, 0])

    def test_join(self):
        u = SimpleIndexingJoin()
        self.compileSimAndStart(u)

        u.b._ag.data.extend([0, 1, 0, 1, None, 1, 0, 1])
        u.c._ag.data.extend([0, 0, 1, 1, None, 1, 1, 0])

        self.runSim(80 * Time.ns)

        self.assertValSequenceEqual(u.a._ag.data,
                                    [0, 1, 2, 3, None, 3, 2, 1])

    def test_rangeJoin(self):
        u = SimpleIndexingRangeJoin()
        self.compileSimAndStart(u)

        u.b._ag.data.extend([0, 3, 0, 3, None, 3, 0, 3])
        u.c._ag.data.extend([0, 0, 3, 3, None, 3, 3, 0])

        self.runSim(80 * Time.ns)

        self.assertValSequenceEqual(u.a._ag.data,
                                    [0, 3, 12, 15, None, 15, 12, 3])

    def test_internSplit(self):
        u = IndexingInernSplit()
        self.compileSimAndStart(u)

        u.a._ag.data.extend([0, 1, 2, 3, None, 3, 0, 3])

        self.runSim(80 * Time.ns)

        self.assertValSequenceEqual(u.b._ag.data,
                                    [0, 1, 2, 3, None, 3, 0, 3])

    def test_internJoin(self):
        u = IndexingInernJoin()
        self.compileSimAndStart(u)

        u.a._ag.data.extend([0, 1, 0, 1, None, 0, 1, 0])
        u.b._ag.data.extend([0, 0, 1, 1, None, 0, 1, 0])

        self.runSim(80 * Time.ns)

        self.assertValSequenceEqual(u.c._ag.data,
                                    [0, 1, 0, 1, None, 0, 1, 0])
        self.assertValSequenceEqual(u.d._ag.data,
                                    [0, 0, 1, 1, None, 0, 1, 0])

    def test_indexingInernRangeSplit(self):
        u = IndexingInernRangeSplit()
        self.compileSimAndStart(u)
        reference = list(range(2 ** 4)) + [None, ]
        u.a._ag.data.extend(reference)

        self.runSim((2 ** 4 + 1) * 10 * Time.ns)

        self.assertValSequenceEqual(u.b._ag.data,
                                    reference)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(IndexingTC('test_split'))
    suite.addTest(unittest.makeSuite(IndexingTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
