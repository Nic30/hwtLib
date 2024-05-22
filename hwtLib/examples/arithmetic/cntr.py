#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwIOs.utils import addClkRst
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override


class Cntr(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(2)

    @override
    def hwDeclr(self):
        addClkRst(self)
        self.en = HwIOSignal()
        self.val = HwIOVectSignal(self.DATA_WIDTH)._m()

    @override
    def hwImpl(self):
        reg = self._reg("counter", HBits(self.DATA_WIDTH), 0)

        # if there is no assignment into reg, value is kept
        If(self.en,
           reg(reg + 1)
        )

        self.val(reg)


if __name__ == "__main__":  # "python main function"
    from hwt.synth import to_rtl_str
    # there is more of synthesis methods. to_rtl_str() returns formated vhdl string
    print(to_rtl_str(Cntr()))
