#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.doc_markers import internal
from hwt.hdl.constants import Time
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.amba.axis_comp.resizer import AxiS_resizer
from pyMathBitPrecise.bit_utils import mask


@internal
def it(dw, *items):
    v = 0
    for item in reversed(items):
        v <<= dw
        v |= item

    return v


class AxiS_resizer_upscale_TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = AxiS_resizer()
        u.USE_STRB = True
        u.DATA_WIDTH = cls.DW_IN = 16
        u.OUT_DATA_WIDTH = cls.DW_OUT = 64
        return u

    def setUp(self):
        super(AxiS_resizer_upscale_TC, self).setUp()
        self.randomize(self.u.dataIn)
        self.randomize(self.u.dataOut)

    def test_nop(self):
        u = self.u
        self.runSim(200 * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)

    def test_simple(self):
        u = self.u

        m = mask(2)
        u.dataIn._ag.data.extend([(1, m, i == 3) for i in range(4)])
        self.runSim(300 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(it(16, 1, 1, 1, 1), it(2, m, m, m, m), 1)])

    def test_noLast(self):
        u = self.u

        m = mask(2)
        u.dataIn._ag.data.extend([(1, m, 0) for _ in range(4)])
        self.runSim(300 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(it(16, 1, 1, 1, 1), it(2, m, m, m, m), 0)])

    def test_multiLast(self):
        u = self.u

        expected = []
        m = mask(2)
        for i in range(4):
            u.dataIn._ag.data.extend([(1, m, i2 == i) for i2 in range(i + 1)])

            expected.append((it(16, *[1 if i2 <= i else 0 for i2 in range(4)]),
                             it(2, *[m if i2 <= i else 0 for i2 in range(4)]),
                             1
                             ))

        self.runSim(700 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    expected)

    def test_noPass(self):
        u = self.u
        u.dataIn._ag.data.extend([(1, mask(2), 0) for _ in range(2)])

        self.runSim(200 * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)


class AxiS_resizer_downscale_TC(SingleUnitSimTestCase):
    @classmethod
    def getUnit(cls):
        u = cls.u = AxiS_resizer()
        u.DATA_WIDTH = cls.DW_IN = 64
        u.OUT_DATA_WIDTH = cls.DW_OUT = 16
        return cls.u

    def setUp(self):
        super(AxiS_resizer_downscale_TC, self).setUp()
        self.randomize(self.u.dataIn)
        self.randomize(self.u.dataOut)

    def test_nop(self):
        u = self.u
        self.runSim(200 * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)

    def test_noLast(self):
        u = self.u

        u.dataIn._ag.data.append((it(16, 1, 2, 3, 4),
                                  it(2, mask(2), mask(2), mask(2), mask(2)),
                                  0))
        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(i + 1, mask(2), 0) for i in range(4)])

    def test_withLast(self):
        u = self.u

        u.dataIn._ag.data.append((it(16, 1, 2, 3, 4),
                                  it(2, mask(2), mask(2), mask(2), mask(2)),
                                  1))
        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(i + 1, mask(2), i == 3)
                                     for i in range(4)])

    def test_onlyPartOfMask(self):
        u = self.u
        u.dataIn._ag.data.append(
            (it(16, 1, 2, 3, 4),
             it(2, mask(2), 0, 0, 0),
             1)
        )
        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(1, mask(2), 1),
                                     ])


class TestComp_AxiS_resizer_downAndUp(AxiS_resizer):
    def _config(self):
        AxiS_resizer._config(self)
        self.INTERNAL_SIZE = Param(8)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = AxiStream()
            self.dataOut = AxiStream()._m()

    def _impl(self):
        self.dataOut(
            AxiSBuilder(self, self.dataIn)
            .resize(self.INTERNAL_SIZE)
            .resize(self.DATA_WIDTH).end)


class AxiS_resizer_downAndUp_TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = TestComp_AxiS_resizer_downAndUp()
        u.DATA_WIDTH = cls.DW = 64
        return u

    def setUp(self):
        super(AxiS_resizer_downAndUp_TC, self).setUp()
        self.randomize(self.u.dataIn)
        self.randomize(self.u.dataOut)

    def test_nop(self):
        u = self.u
        self.runSim(200 * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)

    def test_simple(self):
        u = self.u
        data = [(311 * i, mask(self.DW // 8), i == 2) for i in range(3)]
        u.dataIn._ag.data.extend(data)
        self.runSim(1300 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data, data)


class AxiS_resizer_upAndDown_TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = TestComp_AxiS_resizer_downAndUp()
        u.DATA_WIDTH = cls.DW = 32
        u.INTERNAL_SIZE = 64
        return u

    def setUp(self):
        super(AxiS_resizer_upAndDown_TC, self).setUp()
        self.randomize(self.u.dataIn)
        self.randomize(self.u.dataOut)

    def test_nop(self):
        u = self.u
        self.runSim(200 * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)

    def test_simple(self):
        u = self.u
        data = [(311 * i, mask(self.DW // 8), int(i == 2)) for i in range(3)]
        u.dataIn._ag.data.extend(data)
        self.runSim(1000 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data, data)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_resizer_downscale_TC('test_noLast'))
    suite.addTest(unittest.makeSuite(AxiS_resizer_upscale_TC))
    suite.addTest(unittest.makeSuite(AxiS_resizer_downscale_TC))
    suite.addTest(unittest.makeSuite(AxiS_resizer_downAndUp_TC))
    suite.addTest(unittest.makeSuite(AxiS_resizer_upAndDown_TC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
