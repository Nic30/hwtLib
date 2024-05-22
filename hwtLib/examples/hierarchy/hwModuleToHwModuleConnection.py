#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule

from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.examples.hierarchy.simpleSubHwModule2 import SimpleSubModule2TC
from hwtLib.examples.simpleHwModule2withNonDirectIntConnection import SimpleHwModule2withNonDirectIntConnection


class HwModuleToHwModuleConnection(HwModule):
    """
    .. hwt-autodoc::
    """
    def _config(self):
        self.DATA_WIDTH = HwParam(8)
        self.USE_STRB = HwParam(True)

    def _declr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.a0 = Axi4Stream()
            self.b0 = Axi4Stream()._m()

            self.m0 = SimpleHwModule2withNonDirectIntConnection()
            self.m1 = SimpleHwModule2withNonDirectIntConnection()

    def _impl(self):
        propagateClkRstn(self)
        self.m0.a(self.a0)
        self.m1.a(self.m0.c)
        self.b0(self.m1.c)


class HwModuleToHwModuleConnectionTC(SimpleSubModule2TC):

    @classmethod
    def setUpClass(cls):
        cls.dut = HwModuleToHwModuleConnection()
        cls.compileSim(cls.dut)

if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = HwModuleToHwModuleConnection()
    print(to_rtl_str(m))
