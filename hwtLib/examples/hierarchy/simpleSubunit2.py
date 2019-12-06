#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.examples.simpleAxiStream import SimpleUnitAxiStream


class SimpleSubunit2(Unit):
    """
    .. hwt-schematic::
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


class SimpleSubunit2TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls) -> Unit:
        return SimpleSubunit2()

    def test_simplePass(self):
        u = self.u
        data = [(5, 1, 0), (6, 1, 1)]
        u.a0._ag.data.extend(data)
        self.runSim(50 * Time.ns)
        self.assertEmpty(u.a0._ag.data)
        self.assertValSequenceEqual(u.b0._ag.data, data)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(SimpleSubunit2()))

    import unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SimpleSubunit2TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
