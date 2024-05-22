#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.hObjList import HObjList
from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
from hwt.simulator.simTestCase import SimTestCase
from hwt.synth import synthesised
from hwtLib.amba.axi4Lite import Axi4Lite


class ListOfHwIOsSample3(HwModule):
    """
    Sample unit with HObjList of interfaces (a and b)
    which is not using items of these HObjList of interfacess

    .. hwt-autodoc::
    """

    def _config(self):
        self.SIZE = 3
        Axi4Lite._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            S = self.SIZE
            self.a = HObjList(Axi4Lite() for _ in range(S))
            self.b = HObjList(Axi4Lite() for _ in range(S))._m()

    def _impl(self):
        # directly connect arrays, note that we are not using array items
        # and thats why they are not created
        self.b(self.a)


class ListOfHwIOsSample3b(ListOfHwIOsSample3):
    """
    Sample unit with HObjList of interfaces (a and b)
    which is not using items of these HObjList of interfacess

    .. hwt-autodoc::
    """

    def _impl(self):
        for i in range(int(self.SIZE)):
            self.b[i](self.a[i])


class ListOfHwIOsSample3TC(SimTestCase):

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def test_simplePass(self):
        dut = ListOfHwIOsSample3()
        self._test(dut)

    def test_simplePass_b(self):
        dut = ListOfHwIOsSample3b()
        self._test(dut)

    def _test(self, dut: HwModule):
        self.compileSimAndStart(dut)
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

        pushData(map(lambda ch: ch.aw, dut.a), AW)
        pushData(map(lambda ch: ch.ar, dut.a), AR)
        pushData(map(lambda ch: ch.r, dut.b), R)
        pushData(map(lambda ch: ch.w, dut.a), W)
        pushData(map(lambda ch: ch.b, dut.b), B)

        self.runSim(100 * Time.ns)

        for i in range(3):
            a = dut.a[i]
            b = dut.b[i]
            for hwIO in [a.ar, a.aw, a.w, b.r, b.b]:
                self.assertEmpty(hwIO._ag.data, hwIO)

        checkData(map(lambda ch: ch.aw, dut.b), AW)
        checkData(map(lambda ch: ch.ar, dut.b), AR)
        checkData(map(lambda ch: ch.r, dut.a), R)
        checkData(map(lambda ch: ch.w, dut.b), W)
        checkData(map(lambda ch: ch.b, dut.a), B)

    def test_resources(self):
        dut = ListOfHwIOsSample3()
        expected = {}

        s = ResourceAnalyzer()
        synthesised(dut)
        s.visit_HwModule(dut)
        self.assertDictEqual(s.report(), expected)

    def test_resources_b(self):
        dut = ListOfHwIOsSample3b()
        expected = {}

        s = ResourceAnalyzer()
        synthesised(dut)
        s.visit_HwModule(dut)
        self.assertDictEqual(s.report(), expected)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([ListOfHwIOsSample3TC("test_simplePass")])
    suite = testLoader.loadTestsFromTestCase(ListOfHwIOsSample3TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    from hwt.synth import to_rtl_str
    print(to_rtl_str(ListOfHwIOsSample3b()))
