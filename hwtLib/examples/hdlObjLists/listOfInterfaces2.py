#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit

from hwtLib.amba.axis import AxiStream


class SimpleSubunit(Unit):
    """
    .. hwt-schematic::
    """
    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.USE_STRB = Param(True)

    def _declr(self):
        with self._paramsShared():
            self.c = AxiStream()
            self.d = AxiStream()._m()

    def _impl(self):
        self.d(self.c)


class ListOfInterfacesSample2(Unit):
    """
    Example unit which contains two subunits (u0 and u1)
    and two HObjList of interfacess (a and b)
    first items of this interfaces are connected to u0
    second to u1

    .. hwt-schematic::
    """
    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.USE_STRB = Param(True)

    def _declr(self):
        addClkRstn(self)
        LEN = 2
        with self._paramsShared():
            self.a = HObjList(AxiStream() for _ in range(LEN))
            self.b = HObjList(AxiStream() for _ in range(LEN))._m()

            self.u0 = SimpleSubunit()
            self.u1 = SimpleSubunit()
            # self.u2 = SimpleSubunit()

    def _impl(self):
        self.u0.c(self.a[0])
        self.u1.c(self.a[1])
        # u2in = connect(a[2], u2.c)

        self.b[0](self.u0.d)
        self.b[1](self.u1.d)
        # u2out = connect(u2.d, b[2])


class ListOfInterfacesSample2TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls) -> Unit:
        cls.u = ListOfInterfacesSample2()
        return cls.u

    def test_simplePass(self):
        u = self.u

        # (data, strb, last)
        d0 = [(1, 1, 0),
              (2, 1, 0),
              (3, 1, 1)]
        d1 = [(4, 1, 0),
              (5, 0, 0),
              (6, 1, 1)]
        u.a[0]._ag.data.extend(d0)
        u.a[1]._ag.data.extend(d1)

        self.runSim(50 * Time.ns)

        for i in range(2):
            self.assertEmpty(u.a[i]._ag.data)

        self.assertValSequenceEqual(u.b[0]._ag.data, d0)
        self.assertValSequenceEqual(u.b[1]._ag.data, d1)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(
        toRtl(ListOfInterfacesSample2())
    )

    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(ListOfInterfacesSample2TC('test_simplePass'))
    suite.addTest(unittest.makeSuite(ListOfInterfacesSample2TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
