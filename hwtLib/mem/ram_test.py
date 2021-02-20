#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import WRITE, READ
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.ram import RamSingleClock
from hwtSimApi.constants import CLK_PERIOD


class RamTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = RamSingleClock()
        u.DATA_WIDTH = 8
        u.ADDR_WIDTH = 3
        cls.compileSim(u)

    def test_writeAndRead(self):
        u = self.u
        u.port[0]._ag.requests.extend([(WRITE, 0, 5), (WRITE, 1, 7),
                                 (READ, 0), (READ, 1),
                                 (READ, 0), (READ, 1), (READ, 2)])

        self.runSim(11 * CLK_PERIOD)
        aeq = self.assertValSequenceEqual
        v = [x.read() for x in self.rtl_simulator.model.io.ram_memory]
        aeq(v, [5, 7, None, None, None, None, None, None])
        aeq(u.port[0]._ag.r_data, [5, 7, 5, 7, None])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(RamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
