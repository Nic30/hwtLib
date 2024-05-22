#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override


class InvalidTypeConnetion(HwModule):
    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(32)._m()
        self.b = HwIOVectSignal(64)

    @override
    def hwImpl(self):
        # wrong size can be overridden by dst(src, fit=True)
        self.a(self.b)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = InvalidTypeConnetion()
    # expecting hwt.synthesizer.exceptions.TypeConversionErr
    print(to_rtl_str(m))
