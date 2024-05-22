#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.utils import propagateClkRstn, addClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.abstract.emptyHwModule import EmptyHwModule
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.amba.axis_comp.builder import Axi4SBuilder


class HeadFieldExtractor(EmptyHwModule):
    @override
    def hwDeclr(self):
        self.din = Axi4Stream()
        self.dout = Axi4Stream()._m()
        self.headers = Axi4Stream()._m()


class PatternMatch(EmptyHwModule):
    @override
    def hwDeclr(self):
        self.din = Axi4Stream()
        self.match = Axi4Stream()._m()


class Filter(EmptyHwModule):
    @override
    def hwDeclr(self):
        self.headers = Axi4Stream()
        self.patternMatch = Axi4Stream()

        self.din = Axi4Stream()
        self.dout = Axi4Stream()._m()
        self.cfg = Axi4Lite()


class Exporter(EmptyHwModule):
    @override
    def hwDeclr(self):
        self.din = Axi4Stream()
        self.dout = Axi4Stream()._m()


class NetFilter(HwModule):
    """
    This unit has actually no functionality it is just example
    of hierarchical design.

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(64)

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.din = Axi4Stream()
            self.export = Axi4Stream()._m()
            self.cfg = Axi4Lite()

            self.hfe = HeadFieldExtractor()
            self.patternMatch = PatternMatch()
            self.filter = Filter()
            self.exporter = Exporter()

    @override
    def hwImpl(self):
        s = self
        propagateClkRstn(s)
        Axi4SBuilder(self, s.hfe.dout).split_copy_to(s.patternMatch.din,
                                                    s.filter.din)

        s.hfe.din(s.din)
        s.filter.headers(s.hfe.headers)
        s.filter.patternMatch(s.patternMatch.match)
        s.exporter.din(s.filter.dout)
        s.export(s.exporter.dout)
        self.filter.cfg(s.cfg)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    # from hwt.serializer.ip_packager import IpPackager

    m = NetFilter()
    print(to_rtl_str(m))
    # p = IpPackager(m)
    # p.createPackage("project/ip/")
