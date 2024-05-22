#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIODataVld
from hwt.hwIOs.utils import addClkRstn
from hwt.hObjList import HObjList
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule
from hwt.synth import to_rtl_str
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.examples.hierarchy.hwModuleWrapper import HwModuleWrapper
from hwtLib.examples.base_serialization_TC import BaseSerializationTC


class HwIOArrayExample(HwModule):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        addClkRstn(self)
        self.a = HObjList(Axi4Stream() for _ in range(2))

    def _impl(self):
        for intf in self.a:
            intf.ready(1)


class HwModuleWithParams(HwModule):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = HwParam(64)

    def _declr(self):
        self.din = HwIODataVld()
        self.dout = HwIODataVld()._m()

    def _impl(self):
        self.dout(self.din)


class HwModuleWrapperTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_params_of_base_unit(self):
        m = HwModuleWithParams()
        w = HwModuleWrapper(m)
        self.assert_serializes_as_file(w, "HwModuleWithParams_in_wrap.vhd")

    def test_HwIOs(self):
        m = HwModuleWrapper(HwIOArrayExample())
        to_rtl_str(m)
        self.assertTrue(hasattr(m, "a_0"))
        self.assertTrue(hasattr(m, "a_1"))
        self.assertFalse(hasattr(m, "a"))


if __name__ == "__main__":
    import unittest

    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(HwModuleWrapperTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
