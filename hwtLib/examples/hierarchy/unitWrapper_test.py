#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import VldSynced
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import to_rtl_str
from hwtLib.amba.axis import AxiStream
from hwtLib.examples.hierarchy.unitWrapper import UnitWrapper
from hwtLib.examples.base_serialization_TC import BaseSerializationTC


class ArrayIntfExample(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        addClkRstn(self)
        self.a = HObjList(AxiStream() for _ in range(2))

    def _impl(self):
        for intf in self.a:
            intf.ready(1)


class UnitWithParams(Unit):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.din = VldSynced()
        self.dout = VldSynced()._m()

    def _impl(self):
        self.dout(self.din)


class UnitWrapperTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_params_of_base_unit(self):
        u = UnitWithParams()
        w = UnitWrapper(u)
        self.assert_serializes_as_file(w, "UnitWithParams_in_wrap.vhd")

    def test_interfaces(self):
        u = UnitWrapper(ArrayIntfExample())
        to_rtl_str(u)
        self.assertTrue(hasattr(u, "a_0"))
        self.assertTrue(hasattr(u, "a_1"))
        self.assertFalse(hasattr(u, "a"))


if __name__ == "__main__":
    import unittest

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UnitWrapperTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
