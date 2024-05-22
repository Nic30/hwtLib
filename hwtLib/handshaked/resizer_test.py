#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.constants import Time
from hwt.hwIOs.std import HwIODataRdVld
from hwt.pyUtils.arrayQuery import grouper
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.resizer_test import it
from hwtLib.handshaked.resizer import HsResizer
from pyMathBitPrecise.bit_utils import mask


class HsResizerTC(SimTestCase):

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def test_1to1(self):

        def set_dw(hwIO):
            hwIO.DATA_WIDTH = 32

        dut = HsResizer(HwIODataRdVld, [1, 1],
                      set_dw,
                      set_dw)
        self.compileSimAndStart(dut)
        # self.randomize(dut.dataIn)
        # self.randomize(dut.dataOut)
        N = 10

        d = [self._rand.getrandbits(32) for _ in range(N)]

        dut.dataIn._ag.data.extend(d)

        self.runSim(N * 40 * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data, d)

    def test_1to3(self):

        def set_dw_in(hwIO):
            hwIO.DATA_WIDTH = 32

        def set_dw_out(hwIO):
            hwIO.DATA_WIDTH = 3 * 32

        dut = HsResizer(HwIODataRdVld, [1, 3],
                      set_dw_in,
                      set_dw_out)
        self.compileSimAndStart(dut)
        # self.randomize(dut.dataIn)
        # self.randomize(dut.dataOut)
        N = 9

        d = [self._rand.getrandbits(32) for _ in range(N)]

        dut.dataIn._ag.data.extend(d)

        self.runSim(N * 40 * Time.ns)

        expected = []
        for a, b, c in grouper(3, d):
            v = it(32, a, b, c)
            expected.append(v)

        self.assertValSequenceEqual(dut.dataOut._ag.data, expected)

    def test_3to1(self):

        def set_dw_in(hwIO):
            hwIO.DATA_WIDTH = 3 * 32

        def set_dw_out(hwIO):
            hwIO.DATA_WIDTH = 32

        dut = HsResizer(HwIODataRdVld, [3, 1],
                      set_dw_in,
                      set_dw_out)
        self.compileSimAndStart(dut)
        # self.randomize(dut.dataIn)
        # self.randomize(dut.dataOut)
        N = 9

        d = [self._rand.getrandbits(3 * 32) for _ in range(N)]

        dut.dataIn._ag.data.extend(d)

        self.runSim(3 * N * 40 * Time.ns)

        expected = []
        m = mask(32)
        for a in d:
            expected.extend([a & m, (a >> 32) & m, (a >> 64) & m])

        self.assertValSequenceEqual(dut.dataOut._ag.data, expected)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HsResizerTC("test_1to3")])
    suite = testLoader.loadTestsFromTestCase(HsResizerTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
