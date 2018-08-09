#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.synthesizer.interfaceLevel.emptyUnit import setOut, EmptyUnit
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.builder import AxiSBuilder


class HeadFieldExtractor(EmptyUnit):
    def _declr(self):
        self.din = AxiStream()
        self.dout = AxiStream()
        self.headers = AxiStream()

    def _impl(self):
        setOut(self.dout, self.headers)


class PatternMatch(EmptyUnit):
    def _declr(self):
        self.din = AxiStream()
        self.match = AxiStream()

    def _impl(self):
        setOut(self.match)


class Filter(EmptyUnit):
    def _declr(self):
        self.headers = AxiStream()
        self.patternMatch = AxiStream()

        self.din = AxiStream()
        self.dout = AxiStream()
        self.cfg = Axi4Lite()

    def _impl(self):
        setOut(self.dout)


class Exporter(EmptyUnit):
    def _declr(self):
        self.din = AxiStream()
        self.dout = AxiStream()

    def _impl(self):
        setOut(self.dout)


class NetFilter(Unit):
    """
    This unit has actually no functionality it is just example
    of hierarchical design.
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.din = AxiStream()
            self.export = AxiStream()
            self.cfg = Axi4Lite()

            self.hfe = HeadFieldExtractor()
            self.patternMatch = PatternMatch()
            self.filter = Filter()
            self.exporter = Exporter()

    def _impl(self):
        s = self
        propagateClkRstn(s)
        AxiSBuilder(self, s.hfe.dout).split_copy_to(s.patternMatch.din,
                                                    s.filter.din)

        s.hfe.din(s.din)
        s.filter.headers(s.hfe.headers)
        s.filter.patternMatch(s.patternMatch.match)
        s.exporter.din(s.filter.dout)
        s.export(s.exporter.dout)
        self.filter.cfg(s.cfg)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    # from hwt.serializer.ip_packager.packager import Packager

    u = NetFilter()
    print(toRtl(u))
    # p = Packager(u)
    # p.createPackage("project/ip/")
