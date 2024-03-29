#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.xilinx.locallink.axis_conv import LocalLinkToAxiS, AxiSToLocalLink
from pyMathBitPrecise.bit_utils import mask


class LocalLink_AxiSConvTest(Unit):

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.USER_WIDTH = Param(2)
        self.USE_STRB = Param(True)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = AxiStream()
            self.conv0 = AxiSToLocalLink()
            self.conv1 = LocalLinkToAxiS()
            self.dataOut = AxiStream()._m()

    def _impl(self):
        propagateClkRstn(self)
        self.conv0.dataIn(self.dataIn)
        self.conv1.dataIn(self.conv0.dataOut)
        self.dataOut(self.conv1.dataOut)


class AxiS_localLinkConvTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.u = LocalLink_AxiSConvTest()
        cls.compileSim(cls.u)

    def test_nop(self):
        u = self.u
        self.runSim(200 * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)

    def test_simple(self):
        u = self.u

        # (data, strb, user, last)
        d = [(13, mask(8), 0b01, 0),
             (14, mask(1), 0b10, 1)]

        u.dataIn._ag.data.extend(d)
        self.runSim(200 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data, d)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AxiS_localLinkConvTC("test_withPause")])
    suite = testLoader.loadTestsFromTestCase(AxiS_localLinkConvTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
