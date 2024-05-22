#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.examples.simpleHwModuleAxi4Stream import SimpleHwModuleAxi4Stream


class SimpleSubHwModule2(HwModule):
    """
    .. hwt-autodoc::
    """

    def _config(self) -> None:
        self.USE_STRB = HwParam(True)

    def _declr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.submodule0 = SimpleHwModuleAxi4Stream()
            self.a0 = Axi4Stream()
            self.b0 = Axi4Stream()._m()

        self.a0.DATA_WIDTH = 8
        self.b0.DATA_WIDTH = 8

    def _impl(self):
        propagateClkRstn(self)
        m = self.submodule0
        m.a(self.a0)
        self.b0(m.b)


class SimpleSubModule2TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = SimpleSubHwModule2()
        cls.compileSim(cls.dut)

    def test_simplePass(self):
        dut = self.dut
        data = [(5, 1, 0), (6, 1, 1)]
        dut.a0._ag.data.extend(data)
        self.runSim(50 * Time.ns)
        self.assertEmpty(dut.a0._ag.data)
        self.assertValSequenceEqual(dut.b0._ag.data, data)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(SimpleSubHwModule2()))

    import unittest
    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(SimpleSubModule2TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
