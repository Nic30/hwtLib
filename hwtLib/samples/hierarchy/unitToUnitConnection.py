#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream
from hwtLib.samples.hierarchy.simpleSubunit2 import SimpleSubunit2TC
from hwtLib.samples.simple2withNonDirectIntConnection import Simple2withNonDirectIntConnection


class UnitToUnitConnection(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.a0 = AxiStream()
            self.b0 = AxiStream()

            self.u0 = Simple2withNonDirectIntConnection()
            self.u1 = Simple2withNonDirectIntConnection()

    def _impl(self):
        propagateClkRstn(self)
        self.u0.a ** self.a0
        self.u1.a ** self.u0.c
        self.b0 ** self.u1.c


class UnitToUnitConnectionTC(SimpleSubunit2TC):
    def setUp(self):
        SimTestCase.setUp(self)
        self.u = UnitToUnitConnection()
        self.prepareUnit(self.u)

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(UnitToUnitConnection))
