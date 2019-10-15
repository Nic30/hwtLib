#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal
from hwt.interfaces.utils import addClkRst
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


class Cntr(Unit):
    """
    .. hwt-schematic::
    """
    def _config(self):
        self.DATA_WIDTH = Param(2)

    def _declr(self):
        addClkRst(self)
        self.en = Signal()
        self.val = VectSignal(self.DATA_WIDTH)._m()

    def _impl(self):
        reg = self._reg("counter", Bits(self.DATA_WIDTH), 0)

        # if there is no assignment into reg, value is kept
        If(self.en,
           reg(reg + 1)
        )

        self.val(reg)


if __name__ == "__main__":  # "python main function"
    from hwt.synthesizer.utils import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(Cntr()))
