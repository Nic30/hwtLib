#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl

from hwtLib.amba.axi4Lite import Axi4Lite


class ListOfInterfacesSample3(Unit):
    """
    Sample unit with HObjList of interfaces (a and b)
    which is not using items of these HObjList of interfacess

    .. hwt-schematic::
    """
    def _config(self):
        self.SIZE = 3
        Axi4Lite._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            S = self.SIZE
            self.a = HObjList(Axi4Lite() for _ in range(S))
            self.b = HObjList(Axi4Lite() for _ in range(S))._m()

    def _impl(self):
        # directly connect arrays, note that we are not using array items
        # and thats why they are not created
        self.b(self.a)


class ListOfInterfacesSample3b(ListOfInterfacesSample3):
    """
    Sample unit with HObjList of interfaces (a and b)
    which is not using items of these HObjList of interfacess

    .. hwt-schematic::
    """
    def _impl(self):
        for i in range(int(self.SIZE)):
            self.b[i](self.a[i])


class ListOfInterfacesSample3TC(SimTestCase):

    def test_simplePass(self):
        u = ListOfInterfacesSample3()
        self._test(u)

    def test_simplePass_b(self):
        u = ListOfInterfacesSample3b()
        self._test(u)

    def _test(self, u):
        self.compileSimAndStart(u)
        r = self._rand.getrandbits
        CH_CNT = 3

        def randAddr():
            prot = 0
            return [(r(32), prot) for _ in range(r(2))]

        def randAddr3():
            return [randAddr()
                    for _ in range(CH_CNT)]

        AW = randAddr3()
        AR = randAddr3()
        R = [[(r(32), r(2)), (r(32), r(2))],
             [(r(32), r(2)), (r(32), r(2)), (r(32), r(2))],
             [(r(32), r(2))],
             ]
        W = [[(r(32), r(4)), (r(32), r(4)), (r(32), r(4))],
             [(r(32), r(4)), (r(32), r(4))],
             [(r(32), r(4))]
             ]
        B = [[r(2), ],
             [r(2), r(2), r(2)],
             [r(2), r(2)]
             ]

        def pushData(channels, data):
            """
            Push data to all agents in interface array
            """
            for ch, d in zip(channels, data):
                ch._ag.data.extend(d)

        def checkData(channels, data):
            for ch, d in zip(channels, data):
                self.assertValSequenceEqual(ch._ag.data, d, ch._name)

        pushData(map(lambda ch: ch.aw, u.a), AW)
        pushData(map(lambda ch: ch.ar, u.a), AR)
        pushData(map(lambda ch: ch.r, u.b), R)
        pushData(map(lambda ch: ch.w, u.a), W)
        pushData(map(lambda ch: ch.b, u.b), B)

        self.runSim(100 * Time.ns)

        for i in range(3):
            a = u.a[i]
            b = u.b[i]
            for intf in [a.ar, a.aw, a.w, b.r, b.b]:
                self.assertEmpty(intf._ag.data, intf)

        checkData(map(lambda ch: ch.aw, u.b), AW)
        checkData(map(lambda ch: ch.ar, u.b), AR)
        checkData(map(lambda ch: ch.r, u.a), R)
        checkData(map(lambda ch: ch.w, u.b), W)
        checkData(map(lambda ch: ch.b, u.a), B)

    def test_resources(self):
        u = ListOfInterfacesSample3()
        expected = {}

        s = ResourceAnalyzer()
        toRtl(u, serializer=s)
        self.assertDictEqual(s.report(), expected)

    def test_resources_b(self):
        u = ListOfInterfacesSample3b()
        expected = {}

        s = ResourceAnalyzer()
        toRtl(u, serializer=s)
        self.assertDictEqual(s.report(), expected)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(ListOfInterfacesSample3TC('test_simplePass'))
    suite.addTest(unittest.makeSuite(ListOfInterfacesSample3TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    print(toRtl(ListOfInterfacesSample3b()))
