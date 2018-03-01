#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axi3 import Axi3
from hwtLib.amba.axiLite_comp.endpoint_test import addrGetter
from hwtLib.amba.axi_comp.tester import AxiTester
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem
from hwtLib.amba.sim.axiMemSpaceMaster import AxiLiteMemSpaceMaster


class AxiTesterTC(SimTestCase):
    def setUp(self):
        super(AxiTesterTC, self).setUp()

        self.u = u = AxiTester(Axi3)
        u.DATA_WIDTH.set(32)

        self.prepareUnit(u, onAfterToRtl=self.mkRegisterMap)
        self.m = Axi3DenseMem(u.clk, u.axi)

    def mkRegisterMap(self, u, modelCls):
        bus = u.cntrl
        self.addrProbe = AddressSpaceProbe(bus, addrGetter)
        self.regs = AxiLiteMemSpaceMaster(bus, self.addrProbe.discovered)

    def randomize_all(self):
        axi = self.u.axi

        self.randomize(axi.aw)
        self.randomize(axi.ar)
        self.randomize(axi.w)
        self.randomize(axi.r)
        self.randomize(axi.b)

    def test_nop(self):
        self.randomize_all()
        self.runSim(200 * Time.ns)

    def test_read(self):
        self.randomize_all()
        r = self.regs
        m = self.m

        for _ in range(10):
            memPtr = m.malloc(size, keepOut)
            id_ = self._rand.getrandbits(3)
        r.a_w_id.write(id0)
        r.addr.write()
        self.runSim(200 * Time.ns)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi4_wDatapumpTC('test_singleLong'))
    suite.addTest(unittest.makeSuite(AxiTesterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
