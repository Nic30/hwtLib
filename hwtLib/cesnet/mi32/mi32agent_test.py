#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import READ, WRITE
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit
from hwtLib.cesnet.mi32.intf import Mi32
from pyMathBitPrecise.bit_utils import mask
from hwtSimApi.constants import CLK_PERIOD


class Mi32Wire(Unit):

    def _declr(self):
        addClkRstn(self)
        self.m = Mi32()._m()
        self.s = Mi32()

    def _impl(self):
        self.m(self.s)


class Mi32AgentTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = Mi32Wire()
        cls.compileSim(u)

    def test_nop(self):
        self.runSim(10 * CLK_PERIOD)
        u = self.u
        self.assertEmpty(u.s._ag.addrAg.data)
        self.assertEmpty(u.s._ag.dataAg.data)
        self.assertEmpty(u.m._ag.addrAg.data)
        self.assertEmpty(u.m._ag.dataAg.data)

    def test_read(self):
        u = self.u
        addr_req = [(READ, 0x0), (READ, 0x4), (READ, 0x8)]
        u.s._ag.requests.extend(addr_req)
        data = [1, 2, 3]
        u.m._ag.r_data.extend(data)

        self.runSim(10 * CLK_PERIOD)
        self.assertValSequenceEqual([x[:2] for x in u.m._ag.requests], addr_req)
        self.assertValSequenceEqual(u.s._ag.r_data, data)

    def test_write(self):
        u = self.u
        m = mask(32 // 8)
        ref = [(WRITE, i * 0x4, i + 1, m) for i in range(4)]
        u.s._ag.requests.extend(ref)

        self.runSim(10 * CLK_PERIOD)
        self.assertValSequenceEqual(u.m._ag.requests, ref)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(Mi32AgentTC('test_write'))
    suite.addTest(unittest.makeSuite(Mi32AgentTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
