#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import READ, WRITE
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.avalon.mm import AvalonMM, RESP_OKAY
from hwtLib.avalon.sim.ram import AvalonMmSimRam
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class AvalonMmWire(HwModule):

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.s = AvalonMM()
        self.m = AvalonMM()._m()

    @override
    def hwImpl(self):
        self.m(self.s)


class AvalonMmAgentTC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = AvalonMmWire()
        cls.compileSim(cls.dut)

    def test_nop(self):
        dut = self.dut
        self.runSim(10 * CLK_PERIOD)

        self.assertEmpty(dut.m._ag.req)
        self.assertEmpty(dut.s._ag.rData)
        self.assertEmpty(dut.s._ag.wResp)

    def generate_seq_rw(self, N):
        dut = self.dut
        m = mask(dut.s.DATA_WIDTH // 8)
        STEP = dut.s.DATA_WIDTH // 8

        # rw, address, burstCount, d, be
        inAddr = []
        for i in range(N):
            if (i % 2) == 0:
                rw = READ
                d = None
                be = None
            else:
                rw = WRITE
                d = i
                be = m
            inAddr.append((rw, i * STEP, 1, d, be))

        return inAddr

    def test_pass_data(self, N=8):
        assert N % 2 == 0, N
        dut = self.dut
        inAddr = self.generate_seq_rw(N)
        dut.s._ag.req.extend(inAddr)

        # readData, response
        inR = [
            (i + 1, RESP_OKAY)
            for i in range(N // 2)
        ]
        dut.m._ag.rData.extend(inR)
        inWResp = [RESP_OKAY for _ in range(N // 2)]
        dut.m._ag.wResp.extend(inWResp)

        t = N + 5
        self.runSim(t * CLK_PERIOD)

        ae = self.assertValSequenceEqual
        ae(dut.m._ag.req, inAddr)
        ae(dut.s._ag.rData, inR)
        ae(dut.s._ag.wResp, inWResp)

    def test_sim_ram(self, N=8):
        dut = self.dut
        mem = AvalonMmSimRam(dut.m)
        inAddr = self.generate_seq_rw(N)
        for i in range(N):
            if i % 2 != 0:
                continue
            mem.data[i] = i

        dut.s._ag.req.extend(inAddr)

        t = N + 5
        self.runSim(t * CLK_PERIOD)
        self.assertValSequenceEqual([mem.data[i] for i in range(N)],
                                    [i for i in range(N)])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AvalonMmAgentTC("test_sim_ram")])
    suite = testLoader.loadTestsFromTestCase(AvalonMmAgentTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
