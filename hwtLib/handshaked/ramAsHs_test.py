#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import NOP
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.handshaked.ramAsHs import RamAsHs, RamHsR
from hwtLib.common_nonstd_interfaces.addr_data_hs import AddrDataHs
from hwtLib.mem.ram import RamSingleClock
from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer


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
        self.ram.port[0](self.conv.ram)


class RamAsHs_TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = RamWithHs()
        u.DATA_WIDTH = 32
        u.ADDR_WIDTH = 8
        return cls.u

    def test_nop(self):
        self.runSim(10 * CLK_PERIOD)
        self.assertEmpty(self.u.r.data._ag.data)

    def test_writeAndRead(self, N=10):
        u = self.u
        MAGIC = 87

        u.w._ag.data.extend([(25 + i, MAGIC + i)
                             for i in range(N)])
        u.r.addr._ag.data.extend([NOP for _ in range(N+2)] + [25 + i for i in range(N)])
        self.runSim((10 + 2*N) * CLK_PERIOD)

        self.assertValSequenceEqual(u.r.data._ag.data, [ MAGIC + i for i in range(N)])

    def test_writeAndRead_randomized(self, N=10):
        u = self.u
        MAGIC = 87
        self.randomize(u.w)
        self.randomize(u.r)
        
        u.w._ag.data.extend([(25 + i, MAGIC + i)
                             for i in range(N)])
        
        def read():
            while u.w._ag.data:
                yield Timer(3 * CLK_PERIOD)
            yield Timer(5 * CLK_PERIOD)
            u.r.addr._ag.data.extend([25 + i for i in range(N)])
        self.procs.append(read())
        self.runSim((8 + N) * 3 * CLK_PERIOD)

        self.assertValSequenceEqual(u.r.data._ag.data, [ MAGIC + i for i in range(N)])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    #suite.addTest(RamAsHs_TC('test_writeAndRead_randomized'))
    suite.addTest(unittest.makeSuite(RamAsHs_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
