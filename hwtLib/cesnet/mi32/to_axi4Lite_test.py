#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import READ, WRITE
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axiLite_comp.sim.ram import Axi4LiteSimRam
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.cesnet.mi32.to_axi4Lite import Mi32_to_Axi4Lite
from pyMathBitPrecise.bit_utils import mask
from hwtSimApi.constants import CLK_PERIOD


class Mi32_to_Axi4LiteTC(SimTestCase):

    def randomize_all(self):
        axi_randomize_per_channel(self, self.u.m)

    @classmethod
    def setUpClass(cls):
        u = cls.u = Mi32_to_Axi4Lite()
        u.ADDR_WIDTH = u.DATA_WIDTH = 32
        cls.compileSim(u)

    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u
        self.memory = Axi4LiteSimRam(axi=u.m)
        self.randomize_all()

    def test_read(self):
        u = self.u
        N = 10
        addr_req = [(READ, i * 0x4) for i in range(N)]
        for i in range(N):
            self.memory.data[i] = i + 1
        u.s._ag.requests.extend(addr_req)

        self.runSim(12 * N * CLK_PERIOD)

        data = [i + 1 for i in range(N)]
        self.assertValSequenceEqual(u.s._ag.r_data, data)

    def test_write(self):
        u = self.u
        m = mask(32 // 8)
        N = 10
        addr_req = [(WRITE, i * 0x4, 1 + i, m) for i in range(N)]
        u.s._ag.requests.extend(addr_req)

        self.runSim(12 * N * CLK_PERIOD)
        self.assertEmpty(u.s._ag.r_data)
        ref_data = [i + 1 for i in range(N)]
        data = [self.memory.data[i] for i in range(N)]
        self.assertValSequenceEqual(data, ref_data)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(Mi32_to_Axi4LiteTC('test_write'))
    suite.addTest(unittest.makeSuite(Mi32_to_Axi4LiteTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
