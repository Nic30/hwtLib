#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.struct import HStructField
from hwt.hwIOs.hwIOStruct import HwIOStruct
from hwt.hwIOs.utils import propagateClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axiLite_comp.endpoint_test import AxiLiteEndpointTC
from hwtLib.amba.axi_comp.builder import AxiBuilder


class AxiLiteEpWithReg(HwModule):
    """
    :class:`hwt.hwModule.HwModule` with AxiLiteEndpoint and AxiLiteReg together
    """

    def __init__(self, structTemplate, hwIOCls=Axi4Lite, shouldEnterFn=None):
        BusEndpoint.__init__(self, structTemplate,
                             hwIOCls=hwIOCls,
                             shouldEnterFn=shouldEnterFn)

    @override
    def hwConfig(self):
        BusEndpoint.hwConfig(self)

    def _mkFieldInterface(self, structHwIO: HwIOStruct, field: HStructField):
        return BusEndpoint._mkFieldInterface(self, structHwIO, field)

    @staticmethod
    def _defaultShouldEnterFn(root, field_path):
        return BusEndpoint._defaultShouldEnterFn(root, field_path)

    @override
    def hwDeclr(self):
        BusEndpoint.hwDeclr(self)
        with self._hwParamsShared():
            self.ep = AxiLiteEndpoint(self.STRUCT_TEMPLATE)

    @override
    def hwImpl(self):
        propagateClkRstn(self)
        self.decoded(self.ep.decoded)
        m = AxiBuilder(self, self.bus).buff(addr_items=1, data_items=1).end
        self.ep.bus(m)


class AxiRegTC(AxiLiteEndpointTC):
    @override
    def mySetUp(self, data_width=32):
        dut = self.dut = AxiLiteEpWithReg(self.STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        dut.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.dut, onAfterToRtl=self.mkRegisterMap)
        return dut


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([AxiRegTC("test_singleLong")])
    suite = testLoader.loadTestsFromTestCase(AxiRegTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
