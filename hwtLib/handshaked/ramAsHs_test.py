#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time, NOP
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.handshaked.ramAsHs import RamAsHs, RamHsR
from hwtLib.interfaces.addrDataHs import AddrDataHs
from hwtLib.mem.ram import RamSingleClock


class RamWithHs(RamAsHs):

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.r = RamHsR()
            self.w = AddrDataHs()

            self.conv = RamAsHs()
            self.ram = RamSingleClock()

    def _impl(self):
        propagateClkRstn(self)
        self.conv.r(self.r)
        self.conv.w(self.w)
        self.ram.a(self.conv.ram)


class RamAsHs_TC(SimTestCase):
    def setUp(self):
        super(RamAsHs_TC, self).setUp()
        u = self.u = RamWithHs()
        u.DATA_WIDTH.set(32)
        u.ADDR_WIDTH.set(8)

        self.prepareUnit(u)

    def test_nop(self):
        self.runSim(100 * Time.ns)
        self.assertEmpty(self.u.r.data._ag.data)

    def test_writeAndRead(self):
        u = self.u
        MAGIC = 87

        u.w._ag.data.extend([(25, MAGIC), (26, MAGIC+1)])
        u.r.addr._ag.data.extend([NOP for _ in range(3)] + [25, 26])
        self.runSim(100 * Time.ns)

        self.assertValSequenceEqual(u.r.data._ag.data, [MAGIC, MAGIC+1])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HsJoinFair_2inputs_TC('test_passdata'))
    suite.addTest(unittest.makeSuite(RamAsHs_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
