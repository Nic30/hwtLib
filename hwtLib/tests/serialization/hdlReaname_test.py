#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.synthesizer.unit import Unit
from hwt.interfaces.std import Signal, Handshaked
from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.amba.axis_fullduplex import AxiStreamFullDuplex
from hwtLib.amba.axis import AxiStream
from ipCorePackager.constants import DIRECTION


class SimpleUnitReanamedPort0(Unit):

    def _declr(self):
        self.a = Signal(hdl_name="a_in_hdl")
        self.b = Signal()._m()

    def _impl(self):
        self.b(self.a)


class SimpleUnitReanamedPort1(Unit):

    def _declr(self):
        self.a = Handshaked(hdl_name="a_in_hdl")
        self.b = Handshaked()._m()

    def _impl(self):
        self.b(self.a)


class SimpleUnitReanamedPort2(Unit):

    def _declr(self):
        self.a = Handshaked(hdl_name={"data": "a_in_hdl",
                                      "vld": "a_in_hdl_valid",
                                      "rd": "a_in_hdl_ready"})
        self.b = Handshaked()._m()

    def _impl(self):
        self.b(self.a)


class SimpleUnitReanamedPort3(Unit):

    def _declr(self):
        self.a = Handshaked(hdl_name="")
        self.b = Handshaked()._m()

    def _impl(self):
        self.b(self.a)


class SimpleUnitReanamedPort4(Unit):

    def _declr(self):
        self.a = AxiStreamFullDuplex(hdl_name="")
        self.b = AxiStreamFullDuplex()._m()

    def _impl(self):
        self.b(self.a)


class _AxiStreamFullDuplex(AxiStreamFullDuplex):

    def _declr(self):
        with self._paramsShared():
            if self.HAS_TX:
                self.tx = AxiStream(hdl_name="eth_tx")

            if self.HAS_RX:
                self.rx = AxiStream(masterDir=DIRECTION.IN,
                                    hdl_name={
                                        "data": "eth_rx",
                                        "valid": "eth_rx_vld",
                                    })


class SimpleUnitReanamedPort5(Unit):

    def _declr(self):
        self.a = _AxiStreamFullDuplex(hdl_name="")
        self.b = _AxiStreamFullDuplex()._m()

    def _impl(self):
        self.b(self.a)


class SerializerHdlRename_TC(BaseSerializationTC):
    __FILE__ = __file__

    def test_SimpleUnitReanamedPort0(self):
        self.assert_serializes_as_file(SimpleUnitReanamedPort0(), "SimpleUnitReanamedPort0.vhd")

    def test_SimpleUnitReanamedPort1(self):
        self.assert_serializes_as_file(SimpleUnitReanamedPort1(), "SimpleUnitReanamedPort1.vhd")

    def test_SimpleUnitReanamedPort2(self):
        self.assert_serializes_as_file(SimpleUnitReanamedPort2(), "SimpleUnitReanamedPort2.vhd")

    def test_SimpleUnitReanamedPort3(self):
        self.assert_serializes_as_file(SimpleUnitReanamedPort3(), "SimpleUnitReanamedPort3.vhd")

    def test_SimpleUnitReanamedPort4(self):
        self.assert_serializes_as_file(SimpleUnitReanamedPort4(), "SimpleUnitReanamedPort4.vhd")

    def test_SimpleUnitReanamedPort5(self):
        self.assert_serializes_as_file(SimpleUnitReanamedPort5(), "SimpleUnitReanamedPort5.vhd")


if __name__ == '__main__':
    import unittest

    suite = unittest.TestSuite()
    # suite.addTest(SerializerHdlRename_TC('test_SimpleUnitReanamedPort5'))
    suite.addTest(unittest.makeSuite(SerializerHdlRename_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
