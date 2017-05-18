#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.intfLvl import Unit, Param
from hwtLib.amba.axis import AxiStream
from hwtLib.samples.iLvl.simpleAxiStream import SimpleUnitAxiStream
from hwtLib.samples.iLvl.hierarchy.simpleSubunit2 import SimpleSubunit2TC
from hwt.simulator.simTestCase import SimTestCase
from hwt.interfaces.utils import addClkRstn, propagateClkRstn


class SimpleSubunit3(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(128)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.subunit0 = SimpleUnitAxiStream()

            self.a0 = AxiStream()
            self.b0 = AxiStream()

    def _impl(self):
        propagateClkRstn(self)
        u = self.subunit0
        u.a ** self.a0
        self.b0 ** u.b

class SimpleSubunit3TC(SimpleSubunit2TC):
    def setUp(self):
        SimTestCase.setUp(self)
        self.u = SimpleSubunit3()
        self.prepareUnit(self.u)


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleSubunit3))
