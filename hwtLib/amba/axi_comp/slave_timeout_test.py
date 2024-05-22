#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.slave_timeout import Axi4SlaveTimeout
from hwtLib.amba.constants import RESP_SLVERR, RESP_OKAY
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class Axi4SlaveTimeoutTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = Axi4SlaveTimeout(Axi4)
        dut.TIMEOUT = 4
        cls.compileSim(dut)

    def randomize_all(self):
        dut = self.dut
        for axi in [dut.m, dut.s]:
            axi_randomize_per_channel(self, axi)

    def test_nop(self):
        dut = self.dut
        self.runSim(10 * CLK_PERIOD)
        ae = self.assertEmpty
        ae(dut.m.aw._ag.data)
        ae(dut.m.w._ag.data)
        ae(dut.m.ar._ag.data)

        ae(dut.s.r._ag.data)
        ae(dut.s.b._ag.data)

    def test_read(self):
        dut = self.dut
        ar_req = dut.s.ar._ag.create_addr_req(0x8, 0, _id=1)
        dut.s.ar._ag.data.append(ar_req)
        r_trans = (1, 0x123, RESP_OKAY, 1)
        dut.m.r._ag.data.append(r_trans)

        self.runSim(10 * CLK_PERIOD)
        ae = self.assertEmpty
        ae(dut.m.aw._ag.data)
        ae(dut.m.w._ag.data)
        self.assertValSequenceEqual(dut.m.ar._ag.data, [ar_req, ])
        self.assertValSequenceEqual(dut.s.r._ag.data, [r_trans, ])
        ae(dut.s.b._ag.data)

    def test_read_timeout(self):
        dut = self.dut
        ar_req = dut.s.ar._ag.create_addr_req(0x8, 0, _id=1)
        dut.s.ar._ag.data.append(ar_req)
        self.runSim(10 * CLK_PERIOD)
        ae = self.assertEmpty
        ae(dut.m.aw._ag.data)
        ae(dut.m.w._ag.data)
        self.assertValSequenceEqual(dut.m.ar._ag.data, [ar_req, ])
        self.assertValSequenceEqual(dut.s.r._ag.data, [(1, None, RESP_SLVERR, 1), ])
        ae(dut.s.b._ag.data)

    def test_b_timeout(self):
        dut = self.dut
        aw_req = dut.s.ar._ag.create_addr_req(0x8, 0, _id=1)
        dut.s.aw._ag.data.append(aw_req)
        w_trans = (0x123, mask(dut.m.DATA_WIDTH // 8), 1)
        dut.s.w._ag.data.append(w_trans)

        self.runSim(10 * CLK_PERIOD)
        ae = self.assertEmpty
        self.assertValSequenceEqual(dut.m.aw._ag.data, [aw_req, ])
        self.assertValSequenceEqual(dut.m.w._ag.data, [w_trans, ])
        ae(dut.m.ar._ag.data)
        ae(dut.s.r._ag.data)
        self.assertValSequenceEqual(dut.s.b._ag.data, [((1, RESP_SLVERR))])

    def test_write(self):
        dut = self.dut
        aw_req = dut.s.ar._ag.create_addr_req(0x8, 0, _id=1)
        dut.s.aw._ag.data.append(aw_req)
        w_trans = (0x123, mask(dut.s.DATA_WIDTH // 8), 1)
        dut.s.w._ag.data.append(w_trans)
        b_trans = (1, RESP_OKAY)
        dut.m.b._ag.data.append(b_trans)

        self.runSim(10 * CLK_PERIOD)
        ae = self.assertEmpty
        self.assertValSequenceEqual(dut.m.aw._ag.data, [aw_req, ])
        self.assertValSequenceEqual(dut.m.w._ag.data, [w_trans, ])
        ae(dut.m.ar._ag.data)
        ae(dut.s.r._ag.data)
        self.assertValSequenceEqual(dut.s.b._ag.data, [b_trans, ])


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4SlaveTimeoutTC("test_singleLong")])
    suite = testLoader.loadTestsFromTestCase(Axi4SlaveTimeoutTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)