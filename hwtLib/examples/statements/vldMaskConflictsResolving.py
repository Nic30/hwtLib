#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override


class VldMaskConflictsResolving(HwModule):
    """
    Example how invalid value of condition does not matter
    if it has no effect on result

    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        self.a = HwIOSignal()
        self.b = HwIOSignal()
        self.c = HwIOSignal()._m()

    @override
    def hwImpl(self):
        a = self.a
        b = self.b
        c = self.c

        If(a,
            If(b,
              c(1)
            ).Else(
              c(0)
            )
        ).Else(
            If(b,
              c(1)
            ).Else(
              c(0)
            )
        )


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = VldMaskConflictsResolving()
    print(to_rtl_str(m))
