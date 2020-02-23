#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.sim.ram import Axi4LiteSimRam
from hwtLib.amba.axi_comp.builder import AxiBuilder
from hwtLib.amba.constants import PROT_DEFAULT, RESP_OKAY
from hwtLib.mi32.axi4Lite_to_mi32 import Axi4Lite_to_Mi32
from hwtLib.mi32.intf import Mi32
from hwtLib.mi32.to_axi4Lite import Mi32_to_Axi4Lite
from pycocotb.agents.clk import DEFAULT_CLOCK


class Axi4LiteMi32Bridges(Unit):
    """
    Unit with AxiLiteEndpoint + AxiLiteReg + AxiLite2Mi32 + Mi32_2AxiLite
    """

    def _config(self):
        Mi32._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.s = Axi4Lite()
            self.toMi32 = Axi4Lite_to_Mi32()
            self.toAxi = Mi32_to_Axi4Lite()
            self.m = Axi4Lite()._m()

    def _impl(self):
        propagateClkRstn(self)
        toMi32 = self.toMi32
        toAxi = self.toAxi

        m = AxiBuilder(self, self.s).buff().end
        toMi32.s(m)
        toAxi.s(toMi32.m)
        self.m(AxiBuilder(self, toAxi.m).buff().end)


class Mi32Axi4LiteBrigesTC(SingleUnitSimTestCase):
    @classmethod
    def getUnit(cls):
        u = cls.u = Axi4LiteMi32Bridges()
        return u

    def randomize_all(self):
        u = self.u
        for i in [u.m, u.s]:
            self.randomize(i.ar)
            self.randomize(i.aw)
            self.randomize(i.r)
            self.randomize(i.w)
            self.randomize(i.b)

    def setUp(self):
        SingleUnitSimTestCase.setUp(self)
        u = self.u
        self.memory = Axi4LiteSimRam(u.clk, axi=u.m)

    def test_nop(self):
        self.randomize_all()
        self.runSim(10 * DEFAULT_CLOCK)
        u = self.u
        for i in [u.m, u.s]:
            self.assertEmpty(i.ar._ag.data)
            self.assertEmpty(i.aw._ag.data)
            self.assertEmpty(i.r._ag.data)
            self.assertEmpty(i.w._ag.data)
            self.assertEmpty(i.b._ag.data)

    def test_read(self):
        u = self.u
        N = 10
        a_trans = [(i * 0x4, PROT_DEFAULT) for i in range(N)]
        for i in range(N):
            self.memory.data[i] = i + 1
        u.s.ar._ag.data.extend(a_trans)
        #self.randomize_all()
        self.runSim(N * 10 * DEFAULT_CLOCK)
        u = self.u
        for i in [u.s, u.m]:
            self.assertEmpty(i.aw._ag.data)
            self.assertEmpty(i.w._ag.data)
            self.assertEmpty(i.b._ag.data)

        r_trans = [(i + 1, RESP_OKAY) for i in range(N)]
        self.assertValSequenceEqual(u.s.r._ag.data, r_trans)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Mi32Axi4LiteBrigesTC('test_singleLong'))
    suite.addTest(unittest.makeSuite(Mi32Axi4LiteBrigesTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
