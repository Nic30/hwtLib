#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.hwIOStruct import HwIOStruct
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwtLib.xilinx.ipif.buff import IpifBuff
from hwtLib.xilinx.ipif.endpoint import IpifEndpoint
from hwtLib.xilinx.ipif.endpoint_test import IpifEndpointTC
from hwtLib.xilinx.ipif.hIOIpif import Ipif


class IpifBuffWithEndpoint(HwModule):
    def __init__(self, STRUCT_TEMPLATE):
        super(IpifBuffWithEndpoint, self).__init__()
        self.STRUCT_TEMPLATE = STRUCT_TEMPLATE

    def _config(self):
        self.DATA_WIDTH = HwParam(32)

    def _declr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.bus = Ipif()
            self.reg = IpifBuff()
            self.ep = IpifEndpoint(self.STRUCT_TEMPLATE)
            self.decoded = HwIOStruct(self.STRUCT_TEMPLATE,
                                      tuple(),
                                      self.ep._mkFieldInterface)._m()

    def _impl(self):
        propagateClkRstn(self)
        ep = self.ep
        self.reg.s(self.bus)
        ep.bus(self.reg.m)
        self.decoded(ep.decoded)


class IpifBuffTC(IpifEndpointTC):
    FIELD_ADDR = [0x0, 0x4]

    def mySetUp(self, data_width=32):
        dut = self.dut = IpifBuffWithEndpoint(self.STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        dut.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.dut, onAfterToRtl=self.mkRegisterMap)
        return dut


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([IpifBuffTC("test_read")])
    suite = testLoader.loadTestsFromTestCase(IpifBuffTC)

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
