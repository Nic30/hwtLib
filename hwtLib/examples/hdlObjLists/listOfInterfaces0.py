#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.interfaces.std import VldSynced
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


class ListOfInterfacesSample0(Unit):
    """
    Sample unit with HObjList of interfaces (a and b)
    which is not using items of these HObjList of interfacess
    and connects list directly to another list

    .. hwt-schematic::
    """

    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.LEN = 3

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            L = self.LEN
            self.a = HObjList(VldSynced() for _ in range(L))
            self.b = HObjList(VldSynced() for _ in range(L))._m()

    def _impl(self):
        # directly connect arrays, note that we are not using array items
        # and thats why they are not created
        self.b(self.a)


class ListOfInterfacesSample0SliceOnly(Unit):
    """
    Sample unit with HObjList of interfaces a and three of output interfaces b
    each interface is connected manually

    .. hwt-schematic::
    """

    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.LEN = 3

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.a = HObjList(VldSynced() for _ in range(self.LEN))
            self.b0 = VldSynced()._m()
            self.b1 = VldSynced()._m()
            self.b2 = VldSynced()._m()

    def _impl(self):
        self.b0(self.a[0])
        self.b1(self.a[1])
        self.b2(self.a[2])


class ListOfInterfacesSample0ConcatOnly(Unit):
    """
    Same thing as :class:`.ListOfInterfacesSample0SliceOnly`
    but direction of interfaces is oposite

    .. hwt-schematic::
    """
    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.LEN = 3

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.a0 = VldSynced()
            self.a1 = VldSynced()
            self.a2 = VldSynced()
            self.b = HObjList(VldSynced() for _ in range(self.LEN))._m()

    def _impl(self):
        self.b[0](self.a0)
        self.b[1](self.a1)
        self.b[2](self.a2)


class ListOfInterfacesSample0TC(SimTestCase):

    def test_ListOfInterfacesSample0_simplePass(self):
        u = self.compileSimAndStart(ListOfInterfacesSample0())

        u.a[0]._ag.data.extend([1, 2, 3])
        u.a[1]._ag.data.extend([9])
        u.a[2]._ag.data.extend([10, 11, 12, 13])

        self.runSim(50 * Time.ns)

        for i in range(3):
            self.assertEmpty(u.a[i]._ag.data)

        self.assertValSequenceEqual(u.b[0]._ag.data, [1, 2, 3])
        self.assertValSequenceEqual(u.b[1]._ag.data, [9])
        self.assertValSequenceEqual(u.b[2]._ag.data, [10, 11, 12, 13])

    def test_ListOfInterfacesSample0SliceOnly_simplePass(self):
        u = self.compileSimAndStart(ListOfInterfacesSample0SliceOnly())

        u.a[0]._ag.data.extend([1, 2, 3])
        u.a[1]._ag.data.extend([9])
        u.a[2]._ag.data.extend([10, 11, 12, 13])

        self.runSim(50 * Time.ns)

        for i in range(3):
            self.assertEmpty(u.a[i]._ag.data)

        self.assertValSequenceEqual(u.b0._ag.data, [1, 2, 3])
        self.assertValSequenceEqual(u.b1._ag.data, [9])
        self.assertValSequenceEqual(u.b2._ag.data, [10, 11, 12, 13])

    def test_ListOfInterfacesSample0ConcatOnly_simplePass(self):
        u = self.compileSimAndStart(ListOfInterfacesSample0ConcatOnly())

        u.a0._ag.data.extend([1, 2, 3])
        u.a1._ag.data.extend([9])
        u.a2._ag.data.extend([10, 11, 12, 13])

        self.runSim(50 * Time.ns)

        self.assertEmpty(u.a0._ag.data)
        self.assertEmpty(u.a1._ag.data)
        self.assertEmpty(u.a2._ag.data)

        self.assertValSequenceEqual(u.b[0]._ag.data, [1, 2, 3])
        self.assertValSequenceEqual(u.b[1]._ag.data, [9])
        self.assertValSequenceEqual(u.b[2]._ag.data, [10, 11, 12, 13])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Simple2withNonDirectIntConnectionTC('test_passData'))
    suite.addTest(unittest.makeSuite(ListOfInterfacesSample0TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    from hwt.synthesizer.utils import toRtl
    print(toRtl(ListOfInterfacesSample0()))
