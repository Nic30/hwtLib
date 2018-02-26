#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.statements.vldMaskConflictsResolving import VldMaskConflictsResolving


class VldMaskConflictsResolvingTC(SimTestCase):
    def setUp(self):
        self.u = VldMaskConflictsResolving()
        self.prepareUnit(self.u)

    def test_allCases(self):
        u = self.u
        u.a._ag.data.extend([0, 1, None, 0, 0, 0, 0, 0, 1, None, 0])
        u.b._ag.data.extend([0, 0, 0, 1, None, 0, 0, 0, 1, None, 0])

        self.runSim(120 * Time.ns)

        self.assertValSequenceEqual(u.c._ag.data,
                                    [0, 0, 0, 1, None, 0, 0, 0, 1, None, 0, 0])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(VldMaskConflictsResolvingTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
