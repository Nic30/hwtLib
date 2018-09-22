#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwt.bitmask import mask
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream_withUserAndStrb
from hwtLib.amba.axis_comp.localLinkConv import LocalLinkToAxiS, AxiSToLocalLink
from hwt.synthesizer.param import Param
from hwt.interfaces.utils import addClkRstn, propagateClkRstn


class LocalLinkConvTest(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.USER_WIDTH = Param(2)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = AxiStream_withUserAndStrb()
            self.conv0 = AxiSToLocalLink()
            self.conv1 = LocalLinkToAxiS()
            self.dataOut = AxiStream_withUserAndStrb()._m()

    def _impl(self):
        propagateClkRstn(self)
        self.conv0.dataIn(self.dataIn)
        self.conv1.dataIn(self.conv0.dataOut)
        self.dataOut(self.conv1.dataOut)


class AxiS_localLinkConvTC(SimTestCase):
    def setUp(self):
        super(AxiS_localLinkConvTC, self).setUp()
        u = self.u = LocalLinkConvTest()
        self.prepareUnit(u)

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
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_measuringFifoTC('test_withPause'))
    suite.addTest(unittest.makeSuite(AxiS_localLinkConvTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)