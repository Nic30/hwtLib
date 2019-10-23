#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.interfaces.std import VldSynced
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


class SimpleSubunit(Unit):
    """
    .. hwt-schematic::
    """

    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        with self._paramsShared():
            self.c = VldSynced()
            self.d = VldSynced()._m()

    def _impl(self):
        self.d(self.c)


class ListOfInterfacesSample1(Unit):
    """
    Example unit which contains two subuints (u0 and u1)
    and two HObjList of interfacess (a and b)
    first items of this interfaces are connected to u0
    second to u1

    .. hwt-schematic::
    """

    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        LEN = 2

        addClkRstn(self)
        with self._paramsShared():
            self.a = HObjList(VldSynced() for _ in range(LEN))
            self.b = HObjList(VldSynced() for _ in range(LEN))._m()

            self.u0 = SimpleSubunit()
            self.u1 = SimpleSubunit()
            # self.u2 = SimpleSubunit()

    def _impl(self):
        propagateClkRstn(self)
        self.u0.c(self.a[0])
        self.u1.c(self.a[1])
        # u2in = connect(a[2], u2.c)

        self.b[0](self.u0.d)
        self.b[1](self.u1.d)
        # u2out = connect(u2.d, b[2])


class ListOfInterfacesSample1TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = ListOfInterfacesSample1()
        return cls.u

    def test_simplePass(self):
        u = self.u

        u.a[0]._ag.data.extend([1, 2, 3])
        u.a[1]._ag.data.extend([9, 10])

        self.runSim(50 * Time.ns)

        for i in range(2):
            self.assertEmpty(u.a[i]._ag.data)

        self.assertValSequenceEqual(u.b[0]._ag.data, [1, 2, 3])
        self.assertValSequenceEqual(u.b[1]._ag.data, [9, 10])


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = ListOfInterfacesSample1()
    print(toRtl(u))
