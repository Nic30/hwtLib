#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override


class ConstDriverHwModule(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        self.out0 = HwIOSignal()._m()
        self.out1 = HwIOSignal()._m()

    @override
    def hwImpl(self):
        self.out0(0)
        self.out1(1)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(ConstDriverHwModule()))
