#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import RdSynced
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit
from hwtSimApi.constants import CLK_PERIOD


class RdSyncedPipe(Unit):
    def _declr(self):
        addClkRstn(self)
        self.a = RdSynced()
        self.b = RdSynced()._m()

    def _impl(self):
        self.b(self.a)


class RdSynced_agent_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = RdSyncedPipe()
        cls.compileSim(cls.u)

    def test_basic_data_pass(self):
        u = self.u

        u.a._ag.data.extend(range(10))

        self.runSim(12 * CLK_PERIOD)

        self.assertValSequenceEqual(u.b._ag.data, list(range(10)) + [None])


if __name__ == '__main__':
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(RdSyncedPipe('test_basic_data_pass'))
    suite.addTest(unittest.makeSuite(RdSynced_agent_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
