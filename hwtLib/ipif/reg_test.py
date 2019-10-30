#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.ipif.endpoint import IpifEndpoint
from hwtLib.ipif.endpoint_test import IpifEndpointTC
from hwtLib.ipif.intf import Ipif
from hwtLib.ipif.reg import IpifReg


class IpifRegWithEndpoint(Unit):
    def __init__(self, STRUCT_TEMPLATE):
        super(IpifRegWithEndpoint, self).__init__()
        self.STRUCT_TEMPLATE = STRUCT_TEMPLATE

    def _config(self):
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.bus = Ipif()
            self.reg = IpifReg()
            self.ep = IpifEndpoint(self.STRUCT_TEMPLATE)
            self.decoded = StructIntf(self.STRUCT_TEMPLATE,
                                      self.ep._mkFieldInterface)._m()

    def _impl(self):
        propagateClkRstn(self)
        ep = self.ep
        self.reg.dataIn(self.bus)
        ep.bus(self.reg.dataOut)
        self.decoded(ep.decoded)


class IpifRegTC(IpifEndpointTC):
    FIELD_ADDR = [0x0, 0x4]

    def mySetUp(self, data_width=32):
        u = self.u = IpifRegWithEndpoint(self.STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.u, onAfterToRtl=self.mkRegisterMap)
        return u


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()

    # suite.addTest(IpifRegTC('test_read'))
    suite.addTest(unittest.makeSuite(IpifRegTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
