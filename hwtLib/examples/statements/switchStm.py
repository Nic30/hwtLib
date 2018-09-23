#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Switch
from hwt.interfaces.std import Signal, VectSignal
from hwt.synthesizer.unit import Unit


class SwitchStmUnit(Unit):
    """
    Example which is using switch statement to create multiplexer

    .. hwt-schematic::
    """
    def _declr(self):
        self.sel = VectSignal(3)
        self.out = Signal()._m()
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()

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


if __name__ == "__main__":  # alias python main function
    from hwt.synthesizer.utils import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SwitchStmUnit()))
