#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule


class TwoCntrs(HwModule):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        addClkRstn(self)

        self.a_en = HwIOSignal()
        self.b_en = HwIOSignal()

        self.eq = HwIOSignal()._m()
        self.ne = HwIOSignal()._m()
        self.lt = HwIOSignal()._m()
        self.gt = HwIOSignal()._m()

    def _impl(self):
        index_t = HBits(8, signed=False)

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
    from hwt.synth import to_rtl_str

    m = TwoCntrs()
    print(to_rtl_str(m))
