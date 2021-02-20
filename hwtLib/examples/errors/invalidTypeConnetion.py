#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.synthesizer.unit import Unit
from hwt.interfaces.std import VectSignal


class InvalidTypeConnetion(Unit):
    def _declr(self):
        self.a = VectSignal(32)._m()
        self.b = VectSignal(64)

    def _impl(self):
        # wrong size can be overriden by dst(src, fit=True)
        self.a(self.b)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = InvalidTypeConnetion()
    # expecting hwt.synthesizer.exceptions.TypeConversionErr
    print(to_rtl_str(u))
