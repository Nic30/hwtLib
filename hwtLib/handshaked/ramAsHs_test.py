#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import NOP, READ, WRITE
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.common_nonstd_interfaces.addr_data_hs import AddrDataHs
from hwtLib.handshaked.ramAsHs import RamAsHs, RamHsR
from hwtLib.mem.ram import RamSingleClock
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer


class RamWithHs(RamAsHs):

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            if self.HAS_R:
                self.r = RamHsR()
            if self.HAS_W:
                self.w = AddrDataHs()

            self.conv = RamAsHs()
            r = self.ram = RamSingleClock()
            if not self.HAS_W:
                assert self.INIT_DATA is not None
                assert self.HAS_R
                r.PORT_CNT = (READ,)
            elif not self.HAS_R:
                assert self.HAS_W
                r.PORT_CNT = (WRITE,)

    def _impl(self):
        propagateClkRstn(self)
        if self.HAS_R:
            self.conv.r(self.r)
        if self.HAS_W:
            self.conv.w(self.w)
        self.ram.port[0](self.conv.ram)


class RamAsHs_R_only_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = RamWithHs()
        u.DATA_WIDTH = 16
        u.ADDR_WIDTH = 8
        u.HAS_W = False
        ITEMS = cls.ITEMS = 2 ** u.ADDR_WIDTH
        cls.MAGIC = 99
        u.INIT_DATA = tuple(cls.MAGIC + (i % ITEMS) for i in range(ITEMS))
        cls.compileSim(u)

    def test_read(self, N=100, randomized=True,):
        u = self.u
        t = (10 + N) * CLK_PERIOD
        if randomized:
            self.randomize(u.r.addr)
            self.randomize(u.r.data)
            t *= 3

        ref = []
        _N = N
        ITEMS = self.ITEMS
        while True:
            if _N > ITEMS:
                _N -= ITEMS
                ref.extend(u.INIT_DATA)
            else:
                ref.extend(u.INIT_DATA[:_N])
                break

        u.r.addr._ag.data.extend((i % ITEMS) for i in range(N))
        self.runSim(t)

        self.assertValSequenceEqual(u.r.data._ag.data, ref)


class RamAsHs_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = RamWithHs()
        u.DATA_WIDTH = 32
        u.ADDR_WIDTH = 8
        cls.compileSim(u)

    def test_nop(self):
        self.runSim(10 * CLK_PERIOD)
        self.assertEmpty(self.u.r.data._ag.data)

    def test_writeAndRead(self, N=10):
        u = self.u
        MAGIC = 87

        u.w._ag.data.extend([(25 + i, MAGIC + i)
                             for i in range(N)])
        u.r.addr._ag.data.extend([NOP for _ in range(N + 2)] + [25 + i for i in range(N)])
        self.runSim((10 + 2 * N) * CLK_PERIOD)

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


RamAsHs_TCs = [RamAsHs_TC, RamAsHs_R_only_TC]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(RamAsHs_TC('test_writeAndRead_randomized'))
    for tc in RamAsHs_TCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
