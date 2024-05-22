#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.hwIOStruct import HwIOStruct
from hwt.hwIOs.utils import propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.hdl.types.struct import HStructField
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axiLite_comp.endpoint_test import AxiLiteEndpointTC
from hwtLib.amba.axi_comp.static_remap import Axi4StaticRemap


class AxiLiteEndpointBehindStaticRemap(HwModule):
    def _config(self):
        self.MEM_MAP = HwParam([])

    def __init__(self, structTemplate, hwIOCls=Axi4Lite, shouldEnterFn=BusEndpoint._defaultShouldEnterFn):
        BusEndpoint.__init__(self, structTemplate,
                             hwIOCls=hwIOCls,
                             shouldEnterFn=shouldEnterFn)

    def _mkFieldInterface(self, structHwIO: HwIOStruct, field: HStructField):
        return BusEndpoint._mkFieldInterface(self, structHwIO, field)

    def _declr(self):
        AxiLiteEndpoint._declr(self)
        with self._hwParamsShared():
            self.ep = AxiLiteEndpoint(self.STRUCT_TEMPLATE)
            self.remap = Axi4StaticRemap(Axi4Lite)

    def _impl(self):
        self.remap.s(self.bus)
        self.ep.bus(self.remap.m)
        self.decoded(self.ep.decoded)
        propagateClkRstn(self)


class Axi4StaticRemap1TC(AxiLiteEndpointTC):
    OFFSET = 0x1000
    FIELD_ADDR = [OFFSET + 0x0, OFFSET + 0x4]

    def mySetUp(self, data_width=32, STRUCT_TEMPLATE=None):
        if STRUCT_TEMPLATE is None:
            STRUCT_TEMPLATE = self.STRUCT_TEMPLATE
        dut = self.dut = AxiLiteEndpointBehindStaticRemap(STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        dut.DATA_WIDTH = self.DATA_WIDTH
        o = self.OFFSET
        dut.MEM_MAP = (
            (0x0, o, o),
            (o,   o, 0x0)
        )

        self.compileSimAndStart(self.dut, onAfterToRtl=self.mkRegisterMap)
        return dut


class Axi4StaticRemap2TC(Axi4StaticRemap1TC):
    OFFSET = 0x123
    FIELD_ADDR = [OFFSET + 0x0, OFFSET + 0x4]


Axi4StaticRemapTCs = [
    Axi4StaticRemap1TC,
    Axi4StaticRemap2TC
]

if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4StaticRemap1TC("test_read")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in Axi4StaticRemapTCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
