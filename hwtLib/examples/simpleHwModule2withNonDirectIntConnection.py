#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import Time
from hwt.hwIOs.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule
from hwtLib.amba.axi4s import Axi4Stream


class SimpleHwModule2withNonDirectIntConnection(HwModule):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = HwParam(8)
        self.USE_STRB = HwParam(True)

    def _declr(self):
        addClkRstn(self)

        with self._hwParamsShared():
            self.a = Axi4Stream()
            self.c = Axi4Stream()._m()

    def _impl(self):
        # we have to register interface on this unit first before use
        with self._hwParamsShared():
            self.b = Axi4Stream()
        b = self.b

        b(self.a)
        self.c(b)


class Simple2withNonDirectIntConnectionTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = SimpleHwModule2withNonDirectIntConnection()
        cls.compileSim(cls.dut)

    def test_passData(self):
        dut = self.dut
        # (data, strb, last)
        dut.a._ag.data.extend([
            (1, 1, 0),
            (2, 1, 1)
        ])
        self.runSim(100 * Time.ns)

        self.assertValSequenceEqual(dut.c._ag.data, [
            (1, 1, 0),
            (2, 1, 1)
        ])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Simple2withNonDirectIntConnectionTC("test_passData")])
    suite = testLoader.loadTestsFromTestCase(Simple2withNonDirectIntConnectionTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    from hwt.synth import to_rtl_str
    dut = SimpleHwModule2withNonDirectIntConnection()
    print(to_rtl_str(dut))
