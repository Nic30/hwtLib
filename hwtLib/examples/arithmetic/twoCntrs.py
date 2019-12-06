#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit
from hwt.hdl.types.bits import Bits


class TwoCntrs(Unit):
    """
    .. hwt-schematic::
    """
    def _declr(self):
        addClkRstn(self)

        self.a_en = Signal()
        self.b_en = Signal()

        self.eq = Signal()._m()
        self.ne = Signal()._m()
        self.lt = Signal()._m()
        self.gt = Signal()._m()

    def _impl(self):
        index_t = Bits(8, signed=False)

        a = self._reg("reg_a", index_t, def_val=0)
        b = self._reg("reg_b", index_t, def_val=0)

        If(self.a_en,
           a(a + 1)
        )

        If(self.b_en,
           b(b + 1)
        )

        self.eq(a._eq(b))
        self.ne(a != b)
        self.lt(a < b)
        self.gt(a > b)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl

    u = TwoCntrs()
    print(toRtl(u))
