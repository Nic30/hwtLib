#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hObjList import HObjList
from hwt.hwIOs.std import HwIODataVld
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase


class ListOfHwIOsSample0(HwModule):
    """
    Sample unit with HObjList of interfaces (a and b)
    which is not using items of these HObjList of interfacess
    and connects list directly to another list

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(8)
        self.LEN = 3

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            L = self.LEN
            self.a = HObjList(HwIODataVld() for _ in range(L))
            self.b = HObjList(HwIODataVld() for _ in range(L))._m()

    @override
    def hwImpl(self):
        # directly connect arrays, note that we are not using array items
        # and thats why they are not created
        self.b(self.a)


class ListOfHwIOsSample0SliceOnly(HwModule):
    """
    Sample unit with HObjList of interfaces a and three of output interfaces b
    each interface is connected manually

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(8)
        self.LEN = 3

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.a = HObjList(HwIODataVld() for _ in range(self.LEN))
            self.b0 = HwIODataVld()._m()
            self.b1 = HwIODataVld()._m()
            self.b2 = HwIODataVld()._m()

    @override
    def hwImpl(self):
        self.b0(self.a[0])
        self.b1(self.a[1])
        self.b2(self.a[2])


class ListOfHwIOsSample0ConcatOnly(HwModule):
    """
    Same thing as :class:`.ListOfHwIOsSample0SliceOnly`
    but direction of interfaces is opposite

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(8)
        self.LEN = 3

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.a0 = HwIODataVld()
            self.a1 = HwIODataVld()
            self.a2 = HwIODataVld()
            self.b = HObjList(HwIODataVld() for _ in range(self.LEN))._m()

    @override
    def hwImpl(self):
        self.b[0](self.a0)
        self.b[1](self.a1)
        self.b[2](self.a2)


class ListOfHwIOsSample0TC(SimTestCase):

    @override
    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def test_ListOfHwIOsSample0_simplePass(self):
        dut = self.compileSimAndStart(ListOfHwIOsSample0())

        dut.a[0]._ag.data.extend([1, 2, 3])
        dut.a[1]._ag.data.extend([9])
        dut.a[2]._ag.data.extend([10, 11, 12, 13])

        self.runSim(50 * Time.ns)

        for i in range(3):
            self.assertEmpty(dut.a[i]._ag.data)

        self.assertValSequenceEqual(dut.b[0]._ag.data, [1, 2, 3])
        self.assertValSequenceEqual(dut.b[1]._ag.data, [9])
        self.assertValSequenceEqual(dut.b[2]._ag.data, [10, 11, 12, 13])

    def test_ListOfHwIOsSample0SliceOnly_simplePass(self):
        dut = self.compileSimAndStart(ListOfHwIOsSample0SliceOnly())

        dut.a[0]._ag.data.extend([1, 2, 3])
        dut.a[1]._ag.data.extend([9])
        dut.a[2]._ag.data.extend([10, 11, 12, 13])

        self.runSim(50 * Time.ns)

        for i in range(3):
            self.assertEmpty(dut.a[i]._ag.data)

        self.assertValSequenceEqual(dut.b0._ag.data, [1, 2, 3])
        self.assertValSequenceEqual(dut.b1._ag.data, [9])
        self.assertValSequenceEqual(dut.b2._ag.data, [10, 11, 12, 13])

    def test_ListOfHwIOsSample0ConcatOnly_simplePass(self):
        dut = self.compileSimAndStart(ListOfHwIOsSample0ConcatOnly())

        dut.a0._ag.data.extend([1, 2, 3])
        dut.a1._ag.data.extend([9])
        dut.a2._ag.data.extend([10, 11, 12, 13])

        self.runSim(50 * Time.ns)

        self.assertEmpty(dut.a0._ag.data)
        self.assertEmpty(dut.a1._ag.data)
        self.assertEmpty(dut.a2._ag.data)

        self.assertValSequenceEqual(dut.b[0]._ag.data, [1, 2, 3])
        self.assertValSequenceEqual(dut.b[1]._ag.data, [9])
        self.assertValSequenceEqual(dut.b[2]._ag.data, [10, 11, 12, 13])


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([ListOfHwIOsSample0TC("test_passData")])
    suite = testLoader.loadTestsFromTestCase(ListOfHwIOsSample0TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    from hwt.synth import to_rtl_str
    print(to_rtl_str(ListOfHwIOsSample0()))
