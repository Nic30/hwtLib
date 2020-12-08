#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.interfaces.std import Signal
from hwt.synthesizer.unit import Unit


class VldMaskConflictsResolving(Unit):
    """
    Example how invalid value of condition does not matter
    if it has no effect on result

    .. hwt-autodoc::
    """
    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()._m()

    def _impl(self):
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
    from hwt.synthesizer.utils import to_rtl_str
    u = VldMaskConflictsResolving()
    print(to_rtl_str(u))
