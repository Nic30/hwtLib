#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hwIOs.std import HwIOSignal
from hwt.simulator.simTestCase import SimTestCase
from hwt.hwModule import HwModule


class SimpleHwModuleWithNonDirectIntConncetion(HwModule):
    """
    Example of fact that interfaces does not have to be only extern
    the can be used even for connection inside unit

    .. hwt-autodoc::
    """

    def _declr(self):
        self.a = HwIOSignal()
        self.c = HwIOSignal()._m()

    def _impl(self):
        self.b = HwIOSignal()

        self.b(self.a)
        self.c(self.b)


class SimpleModuleWithNonDirectIntConncetionTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = SimpleHwModuleWithNonDirectIntConncetion()
        cls.compileSim(cls.dut)

    def test_passData(self):
        d = [0, 1, 0, 1, 0]
        dut = self.dut
        dut.a._ag.data.extend(d)
        self.runSim(50 * Time.ns)
        self.assertValSequenceEqual(dut.c._ag.data, d)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([SimpleModuleWithNonDirectIntConncetionTC("test_passData")])
    suite = testLoader.loadTestsFromTestCase(SimpleModuleWithNonDirectIntConncetionTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    from hwt.synth import to_rtl_str
    print(to_rtl_str(SimpleHwModuleWithNonDirectIntConncetion()))
