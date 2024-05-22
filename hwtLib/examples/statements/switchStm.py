#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Switch
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwModule import HwModule


class SwitchStmHwModule(HwModule):
    """
    Example which is using switch statement to create multiplexer

    .. hwt-autodoc::
    """
    def _declr(self):
        self.sel = HwIOVectSignal(3)
        self.out = HwIOSignal()._m()
        self.a = HwIOSignal()
        self.b = HwIOSignal()
        self.c = HwIOSignal()

    def _impl(self):
        Switch(self.sel)\
        .Case(0,
            self.out(self.a)
        ).Case(1,
            self.out(self.b)
        ).Case(2,
            self.out(self.c)
        ).Default(
            self.out(0)
        )


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(SwitchStmHwModule()))
