#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import WRITE, READ
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.ram import RamSingleClock
from hwtSimApi.constants import CLK_PERIOD


class RamTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = RamSingleClock()
        dut.DATA_WIDTH = 8
        dut.ADDR_WIDTH = 3
        cls.compileSim(dut)

    def test_writeAndRead(self):
        dut = self.dut
        dut.port[0]._ag.requests.extend([(WRITE, 0, 5), (WRITE, 1, 7),
                                 (READ, 0), (READ, 1),
                                 (READ, 0), (READ, 1), (READ, 2)])

        self.runSim(11 * CLK_PERIOD)
        aeq = self.assertValSequenceEqual
        v = [x.read() for x in self.rtl_simulator.model.io.ram_memory]
        aeq(v, [5, 7, None, None, None, None, None, None])
        aeq(dut.port[0]._ag.r_data, [5, 7, 5, 7, None])


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([RamTC("test_withStops")])
    suite = testLoader.loadTestsFromTestCase(RamTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
