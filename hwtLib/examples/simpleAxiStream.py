#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream


class SimpleUnitAxiStream(Unit):
    """
    Example of unit with axi stream interface

    .. hwt-schematic::
    """
    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.USE_STRB = Param(True)

    def _declr(self):
        with self._paramsShared():
            self.a = AxiStream()
            self.b = AxiStream()._m()

    def _impl(self):
        self.b(self.a)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = SimpleUnitAxiStream()
    print(toRtl(u))
