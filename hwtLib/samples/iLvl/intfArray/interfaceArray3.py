#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.typeShortcuts import hInt
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import evalParam
from hwtLib.amba.axiLite import AxiLite


class InterfaceArraySample3(Unit):
    """
    Sample unit with array interface (a and b)
    which is not using items of these array interfaces
    """
    def _config(self):
        self.SIZE = hInt(3)
        AxiLite._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.a = AxiLite(multipliedBy=self.SIZE)
            self.b = AxiLite(multipliedBy=self.SIZE)

    def _impl(self):
        # directly connect arrays, note that we are not using array items
        # and thats why they are not created
        self.b ** self.a


class InterfaceArraySample3b(InterfaceArraySample3):
    """
    Sample unit with array interface (a and b)
    which is not using items of these array interfaces
    """
    def _impl(self):
        for i in range(evalParam(self.SIZE).val):
            self.b[i] ** self.a[i]


class InterfaceArraySample3TC(SimTestCase):

    def test_simplePass(self):
        u = InterfaceArraySample3()
        self._test(u)

    def test_simplePass_b(self):
        u = InterfaceArraySample3b()
        self._test(u)

    def _test(self, u):
        self.prepareUnit(u)
        r = self._rand.getrandbits

        def randItns():
            return [r(32) for _ in range(r(2))]

        def randInt3():
            return [randItns() for _ in range(3)]

        AW = randInt3()
        AR = randInt3()
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

        def pushData(channel, data):
            for ch, d in zip(channel, data):
                ch._ag.data.extend(d)

        def checkData(channel, data):
            for ch, d in zip(channel, data):
                self.assertValSequenceEqual(ch._ag.data, d, ch._name)

        pushData(u.a.aw, AW)
        pushData(u.a.ar, AR)
        pushData(u.a.r, R)
        pushData(u.a.w, W)
        pushData(u.a.b, B)

        self.doSim(50 * Time.ns)

        for i in range(3):
            for intf in [u.ar, u.aw, u.w, u.r, u.b]:
                self.assertEmpty(intf[i]._ag.data)

        checkData(u.b.aw, AW)
        checkData(u.b.ar, AR)
        checkData(u.b.r, R)
        checkData(u.b.w, W)
        checkData(u.b.b, B)

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Simple2withNonDirectIntConnectionTC('test_passData'))
    suite.addTest(unittest.makeSuite(InterfaceArraySample3TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    
    #from hwt.synthesizer.shortcuts import toRtl
    #print(toRtl(InterfaceArraySample3b()))
