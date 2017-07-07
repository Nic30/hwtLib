#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axis import AxiStream
from hwt.simulator.simTestCase import SimTestCase
from hwt.hdlObjects.constants import Time
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.interfaceLevel.unit import Unit


class SimpleSubunit(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        with self._paramsShared():
            self.c = AxiStream()
            self.d = AxiStream()

    def _impl(self):
        self.d ** self.c


class InterfaceArraySample2(Unit):
    """
    Example unit which contains two subunits (u0 and u1)
    and two array interfaces (a and b)
    first items of this interfaces are connected to u0
    second to u1
    """
    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        addClkRstn(self)
        LEN = 2
        with self._paramsShared():
            self.a = AxiStream(asArraySize=LEN)
            self.b = AxiStream(asArraySize=LEN)

            self.u0 = SimpleSubunit()
            self.u1 = SimpleSubunit()
            # self.u2 = SimpleSubunit()

    def _impl(self):

        self.u0.c ** self.a[0]
        self.u1.c ** self.a[1]
        # u2in = connect(a[2], u2.c)

        self.b[0] ** self.u0.d
        self.b[1] ** self.u1.d
        # u2out = connect(u2.d, b[2])


class InterfaceArraySample2TC(SimTestCase):
    def setUp(self):
        SimTestCase.setUp(self)
        self.u = InterfaceArraySample2()
        self.prepareUnit(self.u)

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

        self.doSim(50 * Time.ns)

        for i in range(2):
            self.assertEmpty(u.a[i]._ag.data)

        self.assertValSequenceEqual(u.b[0]._ag.data, d0)
        self.assertValSequenceEqual(u.b[1]._ag.data, d1)


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(
        toRtl(InterfaceArraySample2())
    )

    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(InterfaceArraySample2TC('test_simplePass'))
    suite.addTest(unittest.makeSuite(InterfaceArraySample2TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    