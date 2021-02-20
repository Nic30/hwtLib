#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.slave_timeout import AxiSlaveTimeout
from hwtLib.amba.constants import RESP_SLVERR, RESP_OKAY
from pyMathBitPrecise.bit_utils import mask
from hwtSimApi.constants import CLK_PERIOD


class AxiSlaveTimeoutTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = AxiSlaveTimeout(Axi4)
        u.TIMEOUT = 4
        cls.compileSim(u)

    def randomize_all(self):
        u = self.u
        for axi in [u.m, u.s]:
            axi_randomize_per_channel(self, axi)

    def test_nop(self):
        u = self.u
        self.runSim(10 * CLK_PERIOD)
        ae = self.assertEmpty
        ae(u.m.aw._ag.data)
        ae(u.m.w._ag.data)
        ae(u.m.ar._ag.data)

        ae(u.s.r._ag.data)
        ae(u.s.b._ag.data)

    def test_read(self):
        u = self.u
        ar_req = u.s.ar._ag.create_addr_req(0x8, 0, _id=1)
        u.s.ar._ag.data.append(ar_req)
        r_trans = (1, 0x123, RESP_OKAY, 1)
        u.m.r._ag.data.append(r_trans)

        self.runSim(10 * CLK_PERIOD)
        ae = self.assertEmpty
        ae(u.m.aw._ag.data)
        ae(u.m.w._ag.data)
        self.assertValSequenceEqual(u.m.ar._ag.data, [ar_req, ])
        self.assertValSequenceEqual(u.s.r._ag.data, [r_trans, ])
        ae(u.s.b._ag.data)

    def test_read_timeout(self):
        u = self.u
        ar_req = u.s.ar._ag.create_addr_req(0x8, 0, _id=1)
        u.s.ar._ag.data.append(ar_req)
        self.runSim(10 * CLK_PERIOD)
        ae = self.assertEmpty
        ae(u.m.aw._ag.data)
        ae(u.m.w._ag.data)
        self.assertValSequenceEqual(u.m.ar._ag.data, [ar_req, ])
        self.assertValSequenceEqual(u.s.r._ag.data, [(1, None, RESP_SLVERR, 1), ])
        ae(u.s.b._ag.data)

    def test_b_timeout(self):
        u = self.u
        aw_req = u.s.ar._ag.create_addr_req(0x8, 0, _id=1)
        u.s.aw._ag.data.append(aw_req)
        w_trans = (0x123, mask(u.m.DATA_WIDTH // 8), 1)
        u.s.w._ag.data.append(w_trans)

        self.runSim(10 * CLK_PERIOD)
        ae = self.assertEmpty
        self.assertValSequenceEqual(u.m.aw._ag.data, [aw_req, ])
        self.assertValSequenceEqual(u.m.w._ag.data, [w_trans, ])
        ae(u.m.ar._ag.data)
        ae(u.s.r._ag.data)
        self.assertValSequenceEqual(u.s.b._ag.data, [((1, RESP_SLVERR))])

    def test_write(self):
        u = self.u
        aw_req = u.s.ar._ag.create_addr_req(0x8, 0, _id=1)
        u.s.aw._ag.data.append(aw_req)
        w_trans = (0x123, mask(u.s.DATA_WIDTH // 8), 1)
        u.s.w._ag.data.append(w_trans)
        b_trans = (1, RESP_OKAY)
        u.m.b._ag.data.append(b_trans)

        self.runSim(10 * CLK_PERIOD)
        ae = self.assertEmpty
        self.assertValSequenceEqual(u.m.aw._ag.data, [aw_req, ])
        self.assertValSequenceEqual(u.m.w._ag.data, [w_trans, ])
        ae(u.m.ar._ag.data)
        ae(u.s.r._ag.data)
        self.assertValSequenceEqual(u.s.b._ag.data, [b_trans, ])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(AxiSlaveTimeoutTC('test_singleLong'))
    suite.addTest(unittest.makeSuite(AxiSlaveTimeoutTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)