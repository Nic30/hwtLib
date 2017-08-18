#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdlObjects.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param


class Cntr(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(2)

    def _declr(self):
        addClkRstn(self)
        self.en = Signal()
        self.val = VectSignal(self.DATA_WIDTH)

    def _impl(self):
        reg = self._reg("counter", Bits(self.DATA_WIDTH), 0)

        If(self.en,
           reg ** (reg + 1)
        ).Else(
           reg ** reg
        )

        self.val ** reg


if __name__ == "__main__":  # "python main function"
    from hwt.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(Cntr()))