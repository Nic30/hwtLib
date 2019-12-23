#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.denseMem import Axi4LiteDenseMem
from hwtLib.amba.axiLite_comp.reg import AxiLiteReg
from hwtLib.amba.constants import PROT_DEFAULT, RESP_OKAY
from hwtLib.mi32.axiLite2Mi32 import AxiLite2Mi32
from hwtLib.mi32.intf import Mi32
from hwtLib.mi32.mi32_2AxiLite import Mi32_2AxiLite
from pycocotb.agents.clk import DEFAULT_CLOCK


class AxiLiteMi32Bridges(Unit):
    """
    Unit with AxiLiteEndpoint + AxiLiteReg + AxiLite2Mi32 + Mi32_2AxiLite
    """

    def _config(self):
        Mi32._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.m = Axi4Lite()
            self.reg0 = AxiLiteReg(Axi4Lite)
            self.toMi32 = AxiLite2Mi32()
            self.toAxi = Mi32_2AxiLite()
            self.reg1 = AxiLiteReg(Axi4Lite)
            self.s = Axi4Lite()._m()

    def _impl(self):
        propagateClkRstn(self)
        reg0 = self.reg0
        toMi32 = self.toMi32
        toAxi = self.toAxi
        reg1 = self.reg1

        reg0.in_s(self.m)
        toMi32.m(reg0.out_m)
        toAxi.m(toMi32.s)
        reg1.in_s(toAxi.s)
        self.s(reg1.out_m)


class Mi32AxiLiteBrigesTC(SingleUnitSimTestCase):
    @classmethod
    def getUnit(cls):
        u = cls.u = AxiLiteMi32Bridges()
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
        self.memory = Axi4LiteDenseMem(u.clk, axi=u.s)

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
        u.m.ar._ag.data.extend(a_trans)
        #self.randomize_all()
        self.runSim(N * 10 * DEFAULT_CLOCK)
        u = self.u
        for i in [u.m, u.s]:
            self.assertEmpty(i.aw._ag.data)
            self.assertEmpty(i.w._ag.data)
            self.assertEmpty(i.b._ag.data)

        r_trans = [(i + 1, RESP_OKAY) for i in range(N)]
        self.assertValSequenceEqual(u.m.r._ag.data, r_trans)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi4_wDatapumpTC('test_singleLong'))
    suite.addTest(unittest.makeSuite(Mi32AxiLiteBrigesTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
