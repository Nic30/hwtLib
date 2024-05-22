#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hwIOs.std import HwIODataVld
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.hObjList import HObjList
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule


class SimpleSubHwModule1(HwModule):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = HwParam(8)

    def _declr(self):
        with self._hwParamsShared():
            self.c = HwIODataVld()
            self.d = HwIODataVld()._m()

    def _impl(self):
        self.d(self.c)


class ListOfHwIOsSample1(HwModule):
    """
    Example unit which contains two submodules (m0 and m1)
    and two HObjList of interfacess (a and b)
    first items of this interfaces are connected to m0
    second to m1

    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = HwParam(8)

    def _declr(self):
        LEN = 2

        addClkRstn(self)
        with self._hwParamsShared():
            self.a = HObjList(HwIODataVld() for _ in range(LEN))
            self.b = HObjList(HwIODataVld() for _ in range(LEN))._m()

            self.m0 = SimpleSubHwModule1()
            self.m1 = SimpleSubHwModule1()
            # self.u2 = SimpleSubHwModule1()

    def _impl(self):
        propagateClkRstn(self)
        self.m0.c(self.a[0])
        self.m1.c(self.a[1])
        # u2in = u2.c(a[2])

        self.b[0](self.m0.d)
        self.b[1](self.m1.d)
        # u2out = b[2](u2.d)


class ListOfHwIOsSample1TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = ListOfHwIOsSample1()
        cls.compileSim(cls.dut)

    def test_simplePass(self):
        dut = self.dut

        dut.a[0]._ag.data.extend([1, 2, 3])
        dut.a[1]._ag.data.extend([9, 10])

        self.runSim(50 * Time.ns)

        for i in range(2):
            self.assertEmpty(dut.a[i]._ag.data)

        self.assertValSequenceEqual(dut.b[0]._ag.data, [1, 2, 3])
        self.assertValSequenceEqual(dut.b[1]._ag.data, [9, 10])


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = ListOfHwIOsSample1()
    print(to_rtl_str(m))
