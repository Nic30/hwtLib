#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.constants import Time
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.xilinx.locallink.axis_conv import LocalLinkToAxi4S, Axi4SToLocalLink
from pyMathBitPrecise.bit_utils import mask


class LocalLink_Axi4SConvTest(HwModule):

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(64)
        self.USER_WIDTH = HwParam(2)
        self.USE_STRB = HwParam(True)

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = Axi4Stream()
            self.conv0 = Axi4SToLocalLink()
            self.conv1 = LocalLinkToAxi4S()
            self.dataOut = Axi4Stream()._m()

    @override
    def hwImpl(self):
        propagateClkRstn(self)
        self.conv0.dataIn(self.dataIn)
        self.conv1.dataIn(self.conv0.dataOut)
        self.dataOut(self.conv1.dataOut)


class Axi4S_localLinkConvTC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = LocalLink_Axi4SConvTest()
        cls.compileSim(cls.dut)

    def test_nop(self):
        dut = self.dut
        self.runSim(200 * Time.ns)

        self.assertEmpty(dut.dataOut._ag.data)

    def test_simple(self):
        dut = self.dut

        # (data, strb, user, last)
        d = [(13, mask(8), 0b01, 0),
             (14, mask(1), 0b10, 1)]

        dut.dataIn._ag.data.extend(d)
        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data, d)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4S_localLinkConvTC("test_withPause")])
    suite = testLoader.loadTestsFromTestCase(Axi4S_localLinkConvTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
