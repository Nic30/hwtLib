#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import READ, WRITE
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit
from hwtLib.avalon.mm import AvalonMM, RESP_OKAY
from hwtLib.avalon.sim.ram import AvalonMmSimRam
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import mask


class AvalonMmWire(Unit):

    def _declr(self):
        addClkRstn(self)
        self.s = AvalonMM()
        self.m = AvalonMM()._m()

    def _impl(self):
        self.m(self.s)


class AvalonMmAgentTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = AvalonMmWire()
        cls.compileSim(cls.u)

    def test_nop(self):
        u = self.u
        self.runSim(10 * CLK_PERIOD)

        self.assertEmpty(u.m._ag.req)
        self.assertEmpty(u.s._ag.rData)
        self.assertEmpty(u.s._ag.wResp)

    def generate_seq_rw(self, N):
        u = self.u
        m = mask(u.s.DATA_WIDTH // 8)
        STEP = u.s.DATA_WIDTH // 8

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
        u = self.u
        inAddr = self.generate_seq_rw(N)
        u.s._ag.req.extend(inAddr)

        # readData, response
        inR = [
            (i + 1, RESP_OKAY)
            for i in range(N // 2)
        ]
        u.m._ag.rData.extend(inR)
        inWResp = [RESP_OKAY for _ in range(N // 2)]
        u.m._ag.wResp.extend(inWResp)

        t = N + 5
        self.runSim(t * CLK_PERIOD)

        ae = self.assertValSequenceEqual
        ae(u.m._ag.req, inAddr)
        ae(u.s._ag.rData, inR)
        ae(u.s._ag.wResp, inWResp)

    def test_sim_ram(self, N=8):
        u = self.u
        mem = AvalonMmSimRam(u.m)
        inAddr = self.generate_seq_rw(N)
        for i in range(N):
            if i % 2 != 0:
                continue
            mem.data[i] = i

        u.s._ag.req.extend(inAddr)

        t = N + 5
        self.runSim(t * CLK_PERIOD)
        self.assertValSequenceEqual([mem.data[i] for i in range(N)],
                                    [i for i in range(N)])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AvalonMmAgentTC('test_sim_ram'))
    suite.addTest(unittest.makeSuite(AvalonMmAgentTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
