#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal
from hwt.synthesizer.unit import Unit


class ConstDriverUnit(Unit):
    """
    .. hwt-schematic::
    """
    def _declr(self):
        self.out0 = Signal()._m()
        self.out1 = Signal()._m()

    def _impl(self):
        self.out0(0)
        self.out1(1)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(ConstDriverUnit()))
