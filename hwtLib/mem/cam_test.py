#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import NOP
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.cam import Cam
from hwtSimApi.constants import CLK_PERIOD


class CamTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = Cam()
        cls.compileSim(cls.u)

    def test_writeAndMatchTest(self):
        u = self.u
        u.write._ag.data.extend([(0, 1, 1),
                                 (1, 3, 1),
                                 (7, 11, 1),
                                 ])

        # NOPs to wait until data is inserted
        u.match._ag.data.extend([NOP, NOP, NOP, 1, 2, 3, 5, 11, 12])

        self.runSim(16 * CLK_PERIOD)
        self.assertValSequenceEqual(u.out._ag.data,
                                    [1, 0, 2, 0, 128, 0])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(CamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
