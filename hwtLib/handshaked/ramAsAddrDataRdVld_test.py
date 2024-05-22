#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import NOP, READ, WRITE
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.commonHwIO.addr_data import HwIOAddrDataRdVld
from hwtLib.handshaked.ramAsAddrDataRdVld import RamAsAddrDataRdVld, HwIORamRdVldR
from hwtLib.mem.ram import RamSingleClock
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer


class RamWithRdVldSync(RamAsAddrDataRdVld):

    @override
    def hwDeclr(self):
        addClkRstn(self)

        with self._hwParamsShared():
            if self.HAS_R:
                self.r = HwIORamRdVldR()
            if self.HAS_W:
                self.w = HwIOAddrDataRdVld()

            self.conv = RamAsAddrDataRdVld()
            r = self.ram = RamSingleClock()
            if not self.HAS_W:
                assert self.INIT_DATA is not None
                assert self.HAS_R
                r.PORT_CNT = (READ,)
            elif not self.HAS_R:
                assert self.HAS_W
                r.PORT_CNT = (WRITE,)

    @override
    def hwImpl(self):
        propagateClkRstn(self)
        if self.HAS_R:
            self.conv.r(self.r)
        if self.HAS_W:
            self.conv.w(self.w)
        self.ram.port[0](self.conv.ram)


class RamWithRdVldSync_R_only_TC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        dut = cls.dut = RamWithRdVldSync()
        dut.DATA_WIDTH = 16
        dut.ADDR_WIDTH = 8
        dut.HAS_W = False
        ITEMS = cls.ITEMS = 2 ** dut.ADDR_WIDTH
        cls.MAGIC = 99
        dut.INIT_DATA = tuple(cls.MAGIC + (i % ITEMS) for i in range(ITEMS))
        cls.compileSim(dut)

    def test_read(self, N=100, randomized=True,):
        dut = self.dut
        t = (10 + N) * CLK_PERIOD
        if randomized:
            self.randomize(dut.r.addr)
            self.randomize(dut.r.data)
            t *= 3

        ref = []
        _N = N
        ITEMS = self.ITEMS
        while True:
            if _N > ITEMS:
                _N -= ITEMS
                ref.extend(dut.INIT_DATA)
            else:
                ref.extend(dut.INIT_DATA[:_N])
                break

        dut.r.addr._ag.data.extend((i % ITEMS) for i in range(N))
        self.runSim(t)

        self.assertValSequenceEqual(dut.r.data._ag.data, ref)


class RamWithRdVldSync_TC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        dut = cls.dut = RamWithRdVldSync()
        dut.DATA_WIDTH = 32
        dut.ADDR_WIDTH = 8
        cls.compileSim(dut)

    def test_nop(self):
        self.runSim(10 * CLK_PERIOD)
        self.assertEmpty(self.dut.r.data._ag.data)

    def test_writeAndRead(self, N=10):
        dut = self.dut
        MAGIC = 87

        dut.w._ag.data.extend([(25 + i, MAGIC + i)
                             for i in range(N)])
        dut.r.addr._ag.data.extend([NOP for _ in range(N + 2)] + [25 + i for i in range(N)])
        self.runSim((10 + 2 * N) * CLK_PERIOD)

        self.assertValSequenceEqual(dut.r.data._ag.data, [ MAGIC + i for i in range(N)])

    def test_writeAndRead_randomized(self, N=10):
        dut = self.dut
        MAGIC = 87
        self.randomize(dut.w)
        self.randomize(dut.r)

        dut.w._ag.data.extend([(25 + i, MAGIC + i)
                             for i in range(N)])

        def read():
            while dut.w._ag.data:
                yield Timer(3 * CLK_PERIOD)
            yield Timer(5 * CLK_PERIOD)
            dut.r.addr._ag.data.extend([25 + i for i in range(N)])

        self.procs.append(read())
        self.runSim((8 + N) * 3 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.r.data._ag.data, [ MAGIC + i for i in range(N)])


RamWithRdVldSync_TCs = [RamWithRdVldSync_TC, RamWithRdVldSync_R_only_TC]

if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([RamWithRdVldSync_TC("test_writeAndRead_randomized")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in RamWithRdVldSync_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
