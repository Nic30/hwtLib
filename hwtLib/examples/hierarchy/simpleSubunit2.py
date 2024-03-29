#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.examples.simpleAxiStream import SimpleUnitAxiStream


class SimpleSubunit2(Unit):
    """
    .. hwt-autodoc::
    """

    def _config(self) -> None:
        self.USE_STRB = Param(True)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.subunit0 = SimpleUnitAxiStream()
            self.a0 = AxiStream()
            self.b0 = AxiStream()._m()

        self.a0.DATA_WIDTH = 8
        self.b0.DATA_WIDTH = 8

    def _impl(self):
        propagateClkRstn(self)
        u = self.subunit0
        u.a(self.a0)
        self.b0(u.b)


class SimpleSubunit2TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = SimpleSubunit2()
        cls.compileSim(cls.u)

    def test_simplePass(self):
        u = self.u
        data = [(5, 1, 0), (6, 1, 1)]
        u.a0._ag.data.extend(data)
        self.runSim(50 * Time.ns)
        self.assertEmpty(u.a0._ag.data)
        self.assertValSequenceEqual(u.b0._ag.data, data)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    print(to_rtl_str(SimpleSubunit2()))

    import unittest
    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(SimpleSubunit2TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
