#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIOSignal, HwIODataRdVld
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.amba.axi4s_fullduplex import Axi4StreamFullDuplex
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from ipCorePackager.constants import DIRECTION


class SimpleHwModuleRenamedPort0(HwModule):

    @override
    def hwDeclr(self):
        self.a = HwIOSignal(hdlName="a_in_hdl")
        self.b = HwIOSignal()._m()

    @override
    def hwImpl(self):
        self.b(self.a)


class SimpleHwModuleRenamedPort1(HwModule):

    @override
    def hwDeclr(self):
        self.a = HwIODataRdVld(hdlName="a_in_hdl")
        self.b = HwIODataRdVld()._m()

    @override
    def hwImpl(self):
        self.b(self.a)


class SimpleHwModuleRenamedPort2(HwModule):

    @override
    def hwDeclr(self):
        self.a = HwIODataRdVld(hdlName={"data": "a_in_hdl",
                                        "vld": "a_in_hdl_valid",
                                        "rd": "a_in_hdl_ready"})
        self.b = HwIODataRdVld()._m()

    @override
    def hwImpl(self):
        self.b(self.a)


class SimpleHwModuleRenamedPort3(HwModule):

    @override
    def hwDeclr(self):
        self.a = HwIODataRdVld(hdlName="")
        self.b = HwIODataRdVld()._m()

    @override
    def hwImpl(self):
        self.b(self.a)


class SimpleHwModuleRenamedPort4(HwModule):

    @override
    def hwDeclr(self):
        self.a = Axi4StreamFullDuplex(hdlName="")
        self.b = Axi4StreamFullDuplex()._m()

    @override
    def hwImpl(self):
        self.b(self.a)


class _Axi4StreamFullDuplex(Axi4StreamFullDuplex):

    @override
    def hwDeclr(self):
        with self._hwParamsShared():
            if self.HAS_TX:
                self.tx = Axi4Stream(hdlName="eth_tx")

            if self.HAS_RX:
                self.rx = Axi4Stream(masterDir=DIRECTION.IN,
                                     hdlName={
                                         "data": "eth_rx",
                                         "valid": "eth_rx_vld",
                                     })


class SimpleHwModuleRenamedPort5(HwModule):

    @override
    def hwDeclr(self):
        self.a = _Axi4StreamFullDuplex(hdlName="")
        self.b = _Axi4StreamFullDuplex()._m()

    @override
    def hwImpl(self):
        self.b(self.a)


class SerializerHdlRename_TC(BaseSerializationTC):
    __FILE__ = __file__

    def test_SimpleHwModuleRenamedPort0(self):
        self.assert_serializes_as_file(SimpleHwModuleRenamedPort0(), "SimpleHwModuleRenamedPort0.vhd")

    def test_SimpleHwModuleRenamedPort1(self):
        self.assert_serializes_as_file(SimpleHwModuleRenamedPort1(), "SimpleHwModuleRenamedPort1.vhd")

    def test_SimpleHwModuleRenamedPort2(self):
        self.assert_serializes_as_file(SimpleHwModuleRenamedPort2(), "SimpleHwModuleRenamedPort2.vhd")

    def test_SimpleHwModuleRenamedPort3(self):
        self.assert_serializes_as_file(SimpleHwModuleRenamedPort3(), "SimpleHwModuleRenamedPort3.vhd")

    def test_SimpleHwModuleRenamedPort4(self):
        self.assert_serializes_as_file(SimpleHwModuleRenamedPort4(), "SimpleHwModuleRenamedPort4.vhd")

    def test_SimpleHwModuleRenamedPort5(self):
        self.assert_serializes_as_file(SimpleHwModuleRenamedPort5(), "SimpleHwModuleRenamedPort5.vhd")


if __name__ == '__main__':
    import unittest

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([SerializerHdlRename_TC("test_SimpleHwModuleRenamedPort5")])
    suite = testLoader.loadTestsFromTestCase(SerializerHdlRename_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
