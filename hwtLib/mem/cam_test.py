#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time, NOP
from hwt.simulator.agentConnector import valuesToInts
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.cam import Cam


class CamTC(SimTestCase):

    def test_writeAndMatchTest(self):
        u = Cam()
        self.prepareUnit(u)

        u.write._ag.data = [(0, 1, -1),
                            (1, 3, -1),
                            (7, 11, -1)]

        u.match._ag.data = [NOP, NOP, NOP, 1, 2, 3, 5, 11, 12]

        self.doSim(160 * Time.ns)
        self.assertSequenceEqual(valuesToInts(u.out._ag.data),
                                 [1, 0, 2, 0, 128, 0])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(CamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
