#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit

from hwtLib.amba.axis import AxiStream
from hwtLib.examples.hierarchy.simpleSubunit2 import SimpleSubunit2TC
from hwtLib.examples.simpleAxiStream import SimpleUnitAxiStream


class SimpleSubunit3(Unit):
    """
    .. hwt-schematic::
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
    def getUnit(cls) -> Unit:
        return SimpleSubunit3()


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(SimpleSubunit3()))
