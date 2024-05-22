#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.operators.indexing import (
    SimpleIndexingSplit,
    SimpleIndexingJoin,
    SimpleIndexingRangeJoin,
    IndexingInternSplit,
    IndexingInernJoin,
    IndexingInernRangeSplit, AssignmentToRegIndex)
from hwtSimApi.constants import CLK_PERIOD


class IndexingTC(SimTestCase):

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def test_split(self):
        dut = SimpleIndexingSplit()
        self.compileSimAndStart(dut)
        dut.a._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])

        self.runSim(8 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.b._ag.data,
                                    [0, 1, 0, 1, None, 1, 0, 1])
        self.assertValSequenceEqual(dut.c._ag.data,
                                    [0, 0, 1, 1, None, 1, 1, 0])

    def test_join(self):
        dut = SimpleIndexingJoin()
        self.compileSimAndStart(dut)

        dut.b._ag.data.extend([0, 1, 0, 1, None, 1, 0, 1])
        dut.c._ag.data.extend([0, 0, 1, 1, None, 1, 1, 0])

        self.runSim(8 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.a._ag.data,
                                    [0, 1, 2, 3, None, 3, 2, 1])

    def test_rangeJoin(self):
        dut = SimpleIndexingRangeJoin()
        self.compileSimAndStart(dut)

        dut.b._ag.data.extend([0, 3, 0, 3, None, 3, 0, 3])
        dut.c._ag.data.extend([0, 0, 3, 3, None, 3, 3, 0])

        self.runSim(8 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.a._ag.data,
                                    [0, 3, 12, 15, None, 15, 12, 3])

    def test_internSplit(self):
        dut = IndexingInternSplit()
        self.compileSimAndStart(dut)

        dut.a._ag.data.extend([0, 1, 2, 3, None, 3, 0, 3])

        self.runSim(8 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.b._ag.data,
                                    [0, 1, 2, 3, None, 3, 0, 3])

    def test_internJoin(self):
        dut = IndexingInernJoin()
        self.compileSimAndStart(dut)

        dut.a._ag.data.extend([0, 1, 0, 1, None, 0, 1, 0])
        dut.b._ag.data.extend([0, 0, 1, 1, None, 0, 1, 0])

        self.runSim(8 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.c._ag.data,
                                    [0, 1, 0, 1, None, 0, 1, 0])
        self.assertValSequenceEqual(dut.d._ag.data,
                                    [0, 0, 1, 1, None, 0, 1, 0])

    def test_indexingInernRangeSplit(self):
        dut = IndexingInernRangeSplit()
        self.compileSimAndStart(dut)
        reference = list(range(2 ** 4)) + [None, ]
        dut.a._ag.data.extend(reference)

        self.runSim((2 ** 4 + 1) * CLK_PERIOD)

        self.assertValSequenceEqual(dut.b._ag.data,
                                    reference)

    def test_AssignmentToRegIndex(self):
        dut = AssignmentToRegIndex()
        self.compileSimAndStart(dut)
        reference = [0b10, 0b10]
        dut.a._ag.data.extend(reference)

        self.runSim(2 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.b._ag.data,
                                    reference[1:])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([IndexingTC("test_split")])
    suite = testLoader.loadTestsFromTestCase(IndexingTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
