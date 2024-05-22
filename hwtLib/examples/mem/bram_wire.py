#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import READ
from hwt.hwIOs.std import HwIOBramPort_noClk
from hwt.hwIOs.utils import addClkRst
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtSimApi.constants import CLK_PERIOD


class BramWire(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        addClkRst(self)
        self.din = HwIOBramPort_noClk()
        self.dout = HwIOBramPort_noClk()._m()

    @override
    def hwImpl(self):
        self.dout(self.din)


class BramWireTC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = BramWire()
        cls.compileSim(cls.dut)

    def test_read(self):
        dut = self.dut
        dut.dout._ag.mem[1] = 1
        dut.dout._ag.mem[2] = 2

        dut.din._ag.requests.extend([(READ, 1), (READ, 2), (READ, 3)])
        self.runSim(10 * CLK_PERIOD)
        self.assertValSequenceEqual(dut.din._ag.r_data, [1, 2, None])


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([BramWireTC("test_async_resources")])
    suite = testLoader.loadTestsFromTestCase(BramWireTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
