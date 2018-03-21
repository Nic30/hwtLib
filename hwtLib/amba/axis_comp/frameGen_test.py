#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.frameGen import AxisFrameGen
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite_comp.endpoint_test import addrGetter
from hwtLib.amba.sim.axiMemSpaceMaster import AxiLiteMemSpaceMaster


class AxisFrameGenTC(SimTestCase):
    def setUp(self):
        self.u = AxisFrameGen()
        self.prepareUnit(self.u, onAfterToRtl=self.mkRegisterMap)

    def mkRegisterMap(self, u, modelCls):
        self.addrProbe = AddressSpaceProbe(u.cntrl, addrGetter)
        self.regs = AxiLiteMemSpaceMaster(u.cntrl, self.addrProbe.discovered)

    def wReg(self, addr, val):
        aw = self.u.cntrl._ag.aw.data
        w = self.u.cntrl._ag.w.data
        aw.append(addr)
        w.append((val, mask(4)))

    def test_len0(self):
        u = self.u
        self.regs.len.write(0)
        self.regs.enable.write(1)

        # u.dataOut._ag.enable = False
        self.runSim(120 * Time.ns)
        self.assertValSequenceEqual(u.axis_out._ag.data,
                                    [(0, mask(8), 1) for _ in range(6)])

    def test_len1(self):
        u = self.u
        L = 1
        self.regs.len.write(L)
        self.regs.enable.write(1)

        # u.dataOut._ag.enable = False
        self.runSim(120 * Time.ns)
        # self.assertValEqual(self.model.dataOut_data, 1)
        expected = [(L - (i % (L + 1)), mask(8), int((i % (L + 1)) >= L)) for i in range(6)]
        self.assertValSequenceEqual(u.axis_out._ag.data, expected)

    def test_len4(self):
        u = self.u
        L = 4
        self.regs.len.write(L)
        self.regs.enable.write(1)

        # u.dataOut._ag.enable = False
        self.runSim(120 * Time.ns)
        # self.assertValEqual(self.model.dataOut_data, 1)
        expected = [(L - (i % (L + 1)), mask(8), int((i % (L + 1)) >= L)) for i in range(6)]
        self.assertValSequenceEqual(u.axis_out._ag.data, expected)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FifoTC('test_normalOp'))
    suite.addTest(unittest.makeSuite(AxisFrameGenTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
