#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hwIOs.hwIOArray import HwIOArray
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4s import Axi4Stream


class SimpleSubHwModule1(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(8)
        self.USE_STRB = HwParam(True)

    @override
    def hwDeclr(self):
        with self._hwParamsShared():
            self.c = Axi4Stream()
            self.d = Axi4Stream()._m()

    @override
    def hwImpl(self):
        self.d(self.c)


class ListOfHwIOsSample2(HwModule):
    """
    Example unit which contains two subunits (m0 and m1)
    and two HwIOArray of HwIO (a and b)
    first items of this interfaces are connected to m0
    second to m1

    .. hwt-autodoc::
    """
    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(8)
        self.USE_STRB = HwParam(True)

    @override
    def hwDeclr(self):
        addClkRstn(self)
        LEN = 2
        with self._hwParamsShared():
            self.a = HwIOArray(Axi4Stream() for _ in range(LEN))
            self.b = HwIOArray(Axi4Stream() for _ in range(LEN))._m()

            self.m0 = SimpleSubHwModule1()
            self.m1 = SimpleSubHwModule1()
            # self.u2 = SimpleSubHwModule1()

    @override
    def hwImpl(self):
        self.m0.c(self.a[0])
        self.m1.c(self.a[1])
        # u2in = u2.c(a[2])

        self.b[0](self.m0.d)
        self.b[1](self.m1.d)
        # u2out = b[2](u2.d)


class ListOfHwIOsSample2TC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = ListOfHwIOsSample2()
        cls.compileSim(cls.dut)

    def test_simplePass(self):
        dut = self.dut

        # (data, strb, last)
        d0 = [(1, 1, 0),
              (2, 1, 0),
              (3, 1, 1)]
        d1 = [(4, 1, 0),
              (5, 0, 0),
              (6, 1, 1)]
        dut.a[0]._ag.data.extend(d0)
        dut.a[1]._ag.data.extend(d1)

        self.runSim(50 * Time.ns)

        for i in range(2):
            self.assertEmpty(dut.a[i]._ag.data)

        self.assertValSequenceEqual(dut.b[0]._ag.data, d0)
        self.assertValSequenceEqual(dut.b[1]._ag.data, d1)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = ListOfHwIOsSample2()
    print(to_rtl_str(m))

    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([ListOfHwIOsSample2TC("test_simplePass")])
    suite = testLoader.loadTestsFromTestCase(ListOfHwIOsSample2TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
