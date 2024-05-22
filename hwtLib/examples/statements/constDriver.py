#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule


class ConstDriverHwModule(HwModule):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.out0 = HwIOSignal()._m()
        self.out1 = HwIOSignal()._m()

    def _impl(self):
        self.out0(0)
        self.out1(1)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(ConstDriverHwModule()))
