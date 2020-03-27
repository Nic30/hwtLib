#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.struct import HStructField
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axiLite_comp.endpoint_test import AxiLiteEndpointTC
from hwtLib.amba.axi_comp.static_remap import AxiStaticRemap


class AxiLiteEndpointBehindStaticRemap(Unit):
    def _config(self):
        self.MEM_MAP = Param([])

    def __init__(self, structTemplate, intfCls=Axi4Lite, shouldEnterFn=BusEndpoint._defaultShouldEnterFn):
        BusEndpoint.__init__(self, structTemplate,
                             intfCls=intfCls,
                             shouldEnterFn=shouldEnterFn)

    def _mkFieldInterface(self, structIntf: StructIntf, field: HStructField):
        return BusEndpoint._mkFieldInterface(self, structIntf, field)

    def _declr(self):
        AxiLiteEndpoint._declr(self)
        with self._paramsShared():
            self.ep = AxiLiteEndpoint(self.STRUCT_TEMPLATE)
            self.remap = AxiStaticRemap(Axi4Lite)

    def _impl(self):
        self.remap.s(self.bus)
        self.ep.bus(self.remap.m)
        self.decoded(self.ep.decoded)
        propagateClkRstn(self)


class AxiStaticRemap1TC(AxiLiteEndpointTC):
    OFFSET = 0x1000
    FIELD_ADDR = [OFFSET + 0x0, OFFSET + 0x4]

    def mySetUp(self, data_width=32, STRUCT_TEMPLATE=None):
        if STRUCT_TEMPLATE is None:
            STRUCT_TEMPLATE = self.STRUCT_TEMPLATE
        u = self.u = AxiLiteEndpointBehindStaticRemap(STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH = self.DATA_WIDTH
        o = self.OFFSET
        u.MEM_MAP = (
            (0x0, o, o),
            (o,   o, 0x0)
        )

        self.compileSimAndStart(self.u, onAfterToRtl=self.mkRegisterMap)
        return u


class AxiStaticRemap2TC(AxiStaticRemap1TC):
    OFFSET = 0x123
    FIELD_ADDR = [OFFSET + 0x0, OFFSET + 0x4]


AxiStaticRemapTCs = [
    AxiStaticRemap1TC,
    AxiStaticRemap2TC
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(AxiStaticRemap1TC('test_read'))
    for tc in AxiStaticRemapTCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
