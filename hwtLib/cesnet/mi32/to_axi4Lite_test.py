#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import READ, WRITE
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axiLite_comp.sim.ram import Axi4LiteSimRam
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.cesnet.mi32.to_axi4Lite import Mi32_to_Axi4Lite
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class Mi32_to_Axi4LiteTC(SimTestCase):

    def randomize_all(self):
        axi_randomize_per_channel(self, self.dut.m)

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = Mi32_to_Axi4Lite()
        dut.ADDR_WIDTH = dut.DATA_WIDTH = 32
        cls.compileSim(dut)

    def setUp(self):
        SimTestCase.setUp(self)
        dut = self.dut
        self.memory = Axi4LiteSimRam(axi=dut.m)
        self.randomize_all()

    def test_read(self):
        dut = self.dut
        N = 10
        addr_req = [(READ, i * 0x4) for i in range(N)]
        for i in range(N):
            self.memory.data[i] = i + 1
        dut.s._ag.requests.extend(addr_req)

        self.runSim(12 * N * CLK_PERIOD)

        data = [i + 1 for i in range(N)]
        self.assertValSequenceEqual(dut.s._ag.r_data, data)

    def test_write(self):
        dut = self.dut
        m = mask(32 // 8)
        N = 10
        addr_req = [(WRITE, i * 0x4, 1 + i, m) for i in range(N)]
        dut.s._ag.requests.extend(addr_req)

        self.runSim(12 * N * CLK_PERIOD)
        self.assertEmpty(dut.s._ag.r_data)
        ref_data = [i + 1 for i in range(N)]
        data = [self.memory.data[i] for i in range(N)]
        self.assertValSequenceEqual(data, ref_data)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Mi32_to_Axi4LiteTC("test_write")])
    suite = testLoader.loadTestsFromTestCase(Mi32_to_Axi4LiteTC)

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
