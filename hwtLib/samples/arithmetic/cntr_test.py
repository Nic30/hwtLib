#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.hdl.operatorDefs import AllOps
from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.serializer.resourceAnalyzer.resourceTypes import ResourceMUX, \
    ResourceFF
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.utils import toRtl
from hwtLib.samples.arithmetic.cntr import Cntr


class CntrTC(SimTestCase):
    def setUp(self):
        super(CntrTC, self).setUp()
        self.u = Cntr()
        self.prepareUnit(self.u)

    def test_overflow(self):
        u = self.u

        u.en._ag.data.append(1)
        self.runSim(90 * Time.ns)
        self.assertValSequenceEqual(u.val._ag.data,
                                    [0, 1, 2, 3, 0, 1, 2, 3])

    def test_contingWithStops(self):
        u = self.u

        u.en._ag.data.extend([1, 0, 1, 1, 0, 0, 0])
        self.runSim(90 * Time.ns)
        self.assertValSequenceEqual(u.val._ag.data,
                                    [0, 1, 1, 2, 3, 3, 3, 3])

    def test_resources_2b(self):
        u = Cntr()

        expected = {(AllOps.ADD, 2): 1,
                    # 1 for reset, one for en
                    (ResourceMUX, 2, 2): 2,
                    ResourceFF: 2}

        s = ResourceAnalyzer()
        toRtl(u, serializer=s)
        r = s.report()
        self.assertDictEqual(r, expected)

    def test_resources_150b(self):
        u = Cntr()
        u.DATA_WIDTH.set(150)

        expected = {(AllOps.ADD, 150): 1,
                    # 1 for reset, one for en
                    (ResourceMUX, 150, 2): 2,
                    ResourceFF: 150}

        s = ResourceAnalyzer()
        toRtl(u, serializer=s)
        r = s.report()
        self.assertDictEqual(r, expected)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(CntrTC('test_resources_150b'))
    suite.addTest(unittest.makeSuite(CntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
