#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwt.bitmask import mask
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwtLib.amba.axis import AxiStream_withUserAndStrb
from hwtLib.amba.axis_comp.frameLinkConv import FrameLinkToAxiS, AxiSToFrameLink
from hwt.synthesizer.param import Param
from hwt.interfaces.utils import addClkRstn, propagateClkRstn


class FrameLinkConvTest(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.USER_WIDTH = Param(2)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = AxiStream_withUserAndStrb()
            self.conv0 = AxiSToFrameLink()
            self.conv1 = FrameLinkToAxiS()
            self.dataOut = AxiStream_withUserAndStrb()

    def _impl(self):
        propagateClkRstn(self)
        self.conv0.dataIn ** self.dataIn
        self.conv1.dataIn ** self.conv0.dataOut
        self.dataOut ** self.conv1.dataOut


class AxiS_frameLinkConvTC(SimTestCase):
    def setUp(self):
        super(AxiS_frameLinkConvTC, self).setUp()
        u = self.u = FrameLinkConvTest()
        self.prepareUnit(u)

    def test_nop(self):
        u = self.u
        self.doSim(200 * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)

    def test_simple(self):
        u = self.u

        # (data, strb, user, last)
        d = [(13, mask(8), 0b01, 0),
             (14, mask(1), 0b10, 1)]

        u.dataIn._ag.data.extend(d)
        self.doSim(200 * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data, d)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_measuringFifoTC('test_withPause'))
    suite.addTest(unittest.makeSuite(AxiS_frameLinkConvTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
