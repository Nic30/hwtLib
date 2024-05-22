#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import Time
from hwt.doc_markers import internal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.amba.axis_comp.builder import Axi4SBuilder
from hwtLib.amba.axis_comp.resizer import Axi4S_resizer
from pyMathBitPrecise.bit_utils import mask


@internal
def it(dw, *items):
    v = 0
    for item in reversed(items):
        v <<= dw
        v |= item

    return v


class Axi4S_resizer_upscale_TC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        dut = cls.dut = Axi4S_resizer()
        dut.USE_STRB = True
        dut.DATA_WIDTH = cls.DW_IN = 16
        dut.OUT_DATA_WIDTH = cls.DW_OUT = 64
        cls.compileSim(dut)

    def setUp(self):
        super(Axi4S_resizer_upscale_TC, self).setUp()
        self.randomize(self.dut.dataIn)
        self.randomize(self.dut.dataOut)

    def test_nop(self):
        dut = self.dut
        self.runSim(200 * Time.ns)

        self.assertEmpty(dut.dataOut._ag.data)

    def test_simple(self):
        dut = self.dut

        m = mask(2)
        dut.dataIn._ag.data.extend([(1, m, i == 3) for i in range(4)])
        self.runSim(300 * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    [(it(16, 1, 1, 1, 1), it(2, m, m, m, m), 1)])

    def test_noLast(self):
        dut = self.dut

        m = mask(2)
        dut.dataIn._ag.data.extend([(1, m, 0) for _ in range(4)])
        self.runSim(300 * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    [(it(16, 1, 1, 1, 1), it(2, m, m, m, m), 0)])

    def test_multiLast(self):
        dut = self.dut

        expected = []
        m = mask(2)
        for i in range(4):
            dut.dataIn._ag.data.extend([(1, m, i2 == i) for i2 in range(i + 1)])

            expected.append((it(16, *[1 if i2 <= i else 0 for i2 in range(4)]),
                             it(2, *[m if i2 <= i else 0 for i2 in range(4)]),
                             1
                             ))

        self.runSim(700 * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    expected)

    def test_noPass(self):
        dut = self.dut
        dut.dataIn._ag.data.extend([(1, mask(2), 0) for _ in range(2)])

        self.runSim(200 * Time.ns)

        self.assertEmpty(dut.dataOut._ag.data)


class Axi4S_resizer_downscale_TC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        dut = cls.dut = Axi4S_resizer()
        dut.DATA_WIDTH = cls.DW_IN = 64
        dut.OUT_DATA_WIDTH = cls.DW_OUT = 16
        cls.compileSim(dut)

    def setUp(self):
        super(Axi4S_resizer_downscale_TC, self).setUp()
        self.randomize(self.dut.dataIn)
        self.randomize(self.dut.dataOut)

    def test_nop(self):
        dut = self.dut
        self.runSim(200 * Time.ns)

        self.assertEmpty(dut.dataOut._ag.data)

    def test_noLast(self):
        dut = self.dut

        dut.dataIn._ag.data.append((it(16, 1, 2, 3, 4),
                                  it(2, mask(2), mask(2), mask(2), mask(2)),
                                  0))
        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    [(i + 1, mask(2), 0) for i in range(4)])

    def test_withLast(self):
        dut = self.dut

        dut.dataIn._ag.data.append((it(16, 1, 2, 3, 4),
                                  it(2, mask(2), mask(2), mask(2), mask(2)),
                                  1))
        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    [(i + 1, mask(2), i == 3)
                                     for i in range(4)])

    def test_onlyPartOfMask(self):
        dut = self.dut
        dut.dataIn._ag.data.append(
            (it(16, 1, 2, 3, 4),
             it(2, mask(2), 0, 0, 0),
             1)
        )
        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    [(1, mask(2), 1),
                                     ])


class TestComp_Axi4S_resizer_downAndUp(Axi4S_resizer):

    @override
    def hwConfig(self):
        Axi4S_resizer.hwConfig(self)
        self.INTERNAL_SIZE = HwParam(8)

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = Axi4Stream()
            self.dataOut = Axi4Stream()._m()

    @override
    def hwImpl(self):
        self.dataOut(
            Axi4SBuilder(self, self.dataIn)
            .resize(self.INTERNAL_SIZE)
            .resize(self.DATA_WIDTH).end)


class Axi4S_resizer_downAndUp_TC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        dut = cls.dut = TestComp_Axi4S_resizer_downAndUp()
        dut.DATA_WIDTH = cls.DW = 64
        cls.compileSim(dut)

    @override
    def setUp(self):
        super(Axi4S_resizer_downAndUp_TC, self).setUp()
        self.randomize(self.dut.dataIn)
        self.randomize(self.dut.dataOut)

    def test_nop(self):
        dut = self.dut
        self.runSim(200 * Time.ns)

        self.assertEmpty(dut.dataOut._ag.data)

    def test_simple(self):
        dut = self.dut
        data = [(311 * i, mask(self.DW // 8), i == 2) for i in range(3)]
        dut.dataIn._ag.data.extend(data)
        self.runSim(1300 * Time.ns)
        self.assertValSequenceEqual(dut.dataOut._ag.data, data)


class Axi4S_resizer_upAndDown_TC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        dut = cls.dut = TestComp_Axi4S_resizer_downAndUp()
        dut.DATA_WIDTH = cls.DW = 32
        dut.INTERNAL_SIZE = 64
        cls.compileSim(dut)

    @override
    def setUp(self):
        super(Axi4S_resizer_upAndDown_TC, self).setUp()
        self.randomize(self.dut.dataIn)
        self.randomize(self.dut.dataOut)

    def test_nop(self):
        dut = self.dut
        self.runSim(200 * Time.ns)

        self.assertEmpty(dut.dataOut._ag.data)

    def test_simple(self):
        dut = self.dut
        data = [(311 * i, mask(self.DW // 8), int(i == 2)) for i in range(3)]
        dut.dataIn._ag.data.extend(data)
        self.runSim(1000 * Time.ns)
        self.assertValSequenceEqual(dut.dataOut._ag.data, data)


Axi4S_resizer_TCs = [
    Axi4S_resizer_upscale_TC,
    Axi4S_resizer_downscale_TC,
    Axi4S_resizer_downAndUp_TC,
    Axi4S_resizer_upAndDown_TC
]

if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4S_resizer_downscale_TC("test_noLast")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in Axi4S_resizer_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
