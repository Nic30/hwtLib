#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwtLib.amba.axi4s import Axi4Stream


class SimpleHwModuleAxi4Stream(HwModule):
    """
    Example of unit with axi stream interface

    .. hwt-autodoc::
    """
    def _config(self):
        self.DATA_WIDTH = HwParam(8)
        self.USE_STRB = HwParam(True)

    def _declr(self):
        with self._hwParamsShared():
            self.a = Axi4Stream()
            self.b = Axi4Stream()._m()

    def _impl(self):
        self.b(self.a)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = SimpleHwModuleAxi4Stream()
    print(to_rtl_str(m))
