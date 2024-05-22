#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import WRITE, READ
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.ramXor import RamXorSingleClock
from hwtSimApi.constants import CLK_PERIOD


class RamXorSingleClockTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = RamXorSingleClock()
        dut.PORT_CNT = (WRITE, WRITE, READ)
        dut.DATA_WIDTH = 8
        dut.ADDR_WIDTH = 3
        cls.compileSim(dut)

    def test_writeAndRead(self):
        dut = self.dut
        dut.port[0]._ag.requests.extend([
            (WRITE, 0, 5), (WRITE, 1, 7),
        ])
        dut.port[2]._ag.requests.extend([
            (READ, 0), (READ, 1),
            (READ, 0), (READ, 1),
            (READ, 0), (READ, 1), (READ, 2)
        ])

        self.runSim(11 * CLK_PERIOD)
        aeq = self.assertValSequenceEqual
        aeq(dut.port[2]._ag.r_data, [0, 0, 5, 7, 5, 7, 0])


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([RamXorSingleClockTC("test_withStops")])
    suite = testLoader.loadTestsFromTestCase(RamXorSingleClockTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
