#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite_comp.endpoint_test import addrGetter
from hwtLib.amba.axiLite_comp.sim.memSpaceMaster import AxiLiteMemSpaceMaster
from hwtLib.amba.axis_comp.frameGen import Axi4sFrameGen
from pyMathBitPrecise.bit_utils import mask


class AxisFrameGenTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = Axi4sFrameGen()
        cls.compileSim(cls.dut, onAfterToRtl=cls.mkRegisterMap)

    @classmethod
    def mkRegisterMap(cls, u):
        cls.addrProbe = AddressSpaceProbe(u.cntrl, addrGetter)
        cls.regs = AxiLiteMemSpaceMaster(u.cntrl, cls.addrProbe.discovered)

    def wReg(self, addr, val):
        aw = self.dut.cntrl._ag.aw.data
        w = self.dut.cntrl._ag.w.data
        aw.append(addr)
        w.append((val, mask(4)))

    def test_len0(self):
        dut = self.dut
        self.regs.len.write(0)
        self.regs.enable.write(1)

        # dut.dataOut._ag.enable = False
        self.runSim(120 * Time.ns)
        self.assertValSequenceEqual(dut.axis_out._ag.data,
                                    [(0, mask(8), 1) for _ in range(6)])

    def test_len1(self):
        dut = self.dut
        L = 1
        self.regs.len.write(L)
        self.regs.enable.write(1)

        # dut.dataOut._ag.enable = False
        self.runSim(120 * Time.ns)
        # self.assertValEqual(self.model.dataOut_data, 1)
        expected = [(L - (i % (L + 1)),
                    mask(8),
                    int((i % (L + 1)) >= L)) for i in range(6)]
        self.assertValSequenceEqual(dut.axis_out._ag.data, expected)

    def test_len4(self):
        dut = self.dut
        L = 4
        self.regs.len.write(L)
        self.regs.enable.write(1)

        # dut.dataOut._ag.enable = False
        self.runSim(120 * Time.ns)
        # self.assertValEqual(self.model.dataOut_data, 1)
        expected = [(L - (i % (L + 1)),
                     mask(8),
                     int((i % (L + 1)) >= L)) for i in range(6)]
        self.assertValSequenceEqual(dut.axis_out._ag.data, expected)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AxisFrameGenTC("test_normalOp")])
    suite = testLoader.loadTestsFromTestCase(AxisFrameGenTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
