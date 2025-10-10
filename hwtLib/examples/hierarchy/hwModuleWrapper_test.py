#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.hwIOArray import HwIOArray
from hwt.hwIOs.std import HwIODataVld
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.synth import to_rtl_str
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.hierarchy.hwModuleWrapper import HwModuleWrapper


class HwIOArrayExample(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.a = HwIOArray(Axi4Stream() for _ in range(2))

    @override
    def hwImpl(self):
        for intf in self.a:
            intf.ready(1)


class HwModuleWithParams(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(64)

    @override
    def hwDeclr(self):
        self.din = HwIODataVld()
        self.dout = HwIODataVld()._m()

    @override
    def hwImpl(self):
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
        self.assertTrue(hasattr(m, "a"))
        self.assertTrue(len(m.a) == 2)
        self.assertTrue(hasattr(m.a, "0"))
        self.assertTrue(hasattr(m.a, "1"))


if __name__ == "__main__":
    import unittest

    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(HwModuleWrapperTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
