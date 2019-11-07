#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import NOP
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.mem.cam import Cam
from pyMathBitPrecise.bit_utils import mask
from pycocotb.constants import CLK_PERIOD


class CamTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = Cam()
        return cls.u

    def test_writeAndMatchTest(self):
        u = self.u
        m = mask(36)
        u.write._ag.data.extend([(0, 1, m),
                                 (1, 3, m),
                                 (7, 11, m)])

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
