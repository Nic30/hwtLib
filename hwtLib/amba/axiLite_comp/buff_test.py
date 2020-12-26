#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.struct import HStructField
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import propagateClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axiLite_comp.endpoint_test import AxiLiteEndpointTC
from hwtLib.amba.axi_comp.builder import AxiBuilder


class AxiLiteEpWithReg(Unit):
    """
    :class:`hwt.synthesizer.unit.Unit` with AxiLiteEndpoint and AxiLiteReg together
    """

    def __init__(self, structTemplate, intfCls=Axi4Lite, shouldEnterFn=None):
        BusEndpoint.__init__(self, structTemplate,
                             intfCls=intfCls,
                             shouldEnterFn=shouldEnterFn)

    def _config(self):
        BusEndpoint._config(self)

    def _mkFieldInterface(self, structIntf: StructIntf, field: HStructField):
        return BusEndpoint._mkFieldInterface(self, structIntf, field)

    @staticmethod
    def _defaultShouldEnterFn(root, field_path):
        return BusEndpoint._defaultShouldEnterFn(root, field_path)

    def _declr(self):
        BusEndpoint._declr(self)
        with self._paramsShared():
            self.ep = AxiLiteEndpoint(self.STRUCT_TEMPLATE)

    def _impl(self):
        propagateClkRstn(self)
        self.decoded(self.ep.decoded)
        m = AxiBuilder(self, self.bus).buff(addr_items=1, data_items=1).end
        self.ep.bus(m)


class AxiRegTC(AxiLiteEndpointTC):
    def mySetUp(self, data_width=32):
        u = self.u = AxiLiteEpWithReg(self.STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH = self.DATA_WIDTH

        self.compileSimAndStart(self.u, onAfterToRtl=self.mkRegisterMap)
        return u


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi4_wDatapumpTC('test_singleLong'))
    suite.addTest(unittest.makeSuite(AxiRegTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
