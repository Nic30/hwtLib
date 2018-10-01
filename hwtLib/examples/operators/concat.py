#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat
from hwt.interfaces.std import Signal, VectSignal
from hwt.synthesizer.unit import Unit


class SimpleConcat(Unit):
    """
    .. hwt-schematic::
    """
    def _declr(self):
        self.a0 = Signal()
        self.a1 = Signal()
        self.a2 = Signal()
        self.a3 = Signal()

        self.a_out = VectSignal(4)._m()

    def _impl(self):
        self.a_out(Concat(self.a3, self.a2, self.a1, self.a0))


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(SimpleConcat))
