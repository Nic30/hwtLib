#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit

from hwtLib.amba.axis import AxiStream
from hwtLib.examples.hierarchy.simpleSubunit2 import SimpleSubunit2TC
from hwtLib.examples.simpleAxiStream import SimpleUnitAxiStream


class SimpleSubunit3(Unit):
    """
    .. hwt-autodoc::
    """
    def _config(self):
        self.DATA_WIDTH = Param(128)
        self.USE_STRB = Param(True)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.subunit0 = SimpleUnitAxiStream()

            self.a0 = AxiStream()
            self.b0 = AxiStream()._m()

    def _impl(self):
        propagateClkRstn(self)
        u = self.subunit0
        u.a(self.a0)
        self.b0(u.b)


class SimpleSubunit3TC(SimpleSubunit2TC):

    @classmethod
    def setUpClass(cls):
        cls.u = SimpleSubunit3()
        cls.compileSim(cls.u)

if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    print(to_rtl_str(SimpleSubunit3()))
