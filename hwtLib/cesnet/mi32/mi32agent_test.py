#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import READ, WRITE
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.cesnet.mi32.intf import Mi32
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class Mi32Wire(HwModule):

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.m = Mi32()._m()
        self.s = Mi32()

    @override
    def hwImpl(self):
        self.m(self.s)


class Mi32AgentTC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        dut = cls.dut = Mi32Wire()
        cls.compileSim(dut)

    def test_nop(self):
        self.runSim(10 * CLK_PERIOD)
        dut = self.dut
        self.assertEmpty(dut.s._ag.addrAg.data)
        self.assertEmpty(dut.s._ag.dataAg.data)
        self.assertEmpty(dut.m._ag.addrAg.data)
        self.assertEmpty(dut.m._ag.dataAg.data)

    def test_read(self):
        dut = self.dut
        addr_req = [(READ, 0x0), (READ, 0x4), (READ, 0x8)]
        dut.s._ag.requests.extend(addr_req)
        data = [1, 2, 3]
        dut.m._ag.r_data.extend(data)

        self.runSim(10 * CLK_PERIOD)
        self.assertValSequenceEqual([x[:2] for x in dut.m._ag.requests], addr_req)
        self.assertValSequenceEqual(dut.s._ag.r_data, data)

    def test_write(self):
        dut = self.dut
        m = mask(32 // 8)
        ref = [(WRITE, i * 0x4, i + 1, m) for i in range(4)]
        dut.s._ag.requests.extend(ref)

        self.runSim(10 * CLK_PERIOD)
        self.assertValSequenceEqual(dut.m._ag.requests, ref)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Mi32AgentTC("test_write")])
    suite = testLoader.loadTestsFromTestCase(Mi32AgentTC)

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
