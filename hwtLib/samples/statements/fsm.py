#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import FsmBuilder, Switch, If
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.std import Signal, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl


class FsmExample(Unit):
    """
    .. hwt-schematic::
    """
    def _declr(self):
        addClkRstn(self)
        self.a = Signal()
        self.b = Signal()
        self.dout = VectSignal(3)._m()

    def _impl(self):
        stT = HEnum("st_t", ["a", "b", "aAndB"])

        a = self.a
        b = self.b
        out = self.dout

        st = FsmBuilder(self, stT)\
        .Trans(stT.a,
            (a & b, stT.aAndB),
            (b, stT.b)
        ).Trans(stT.b,
            (a & b, stT.aAndB),
            (a, stT.a)
        ).Trans(stT.aAndB,
            (a & ~b, stT.a),
            (~a & b, stT.b),
        ).stateReg

        Switch(st)\
        .Case(stT.a,
              out(1)
        ).Case(stT.b,
              out(2)
        ).Case(stT.aAndB,
              out(3)
        )


class HadrcodedFsmExample(FsmExample):
    """
    .. hwt-schematic::
    """
    def _impl(self):
        a = self.a
        b = self.b
        out = self.dout

        st = self._reg("st", Bits(3), 1)

        If(st._eq(1),
            If(a & b,
                st(3)
            ).Elif(b,
                st(2)
            )
        ).Elif(st._eq(2),
            If(a & b,
               st(3)
            ).Elif(a,
                st(1)
            )
        ).Elif(st._eq(3),
            If(a & ~b,
               st(1)
            ).Elif(~a & b,
                st(2)
            )
        ).Else(
            st(1)
        )

        Switch(st)\
        .Case(1,
            out(1)
        ).Case(2,
            out(2)
        ).Case(3,
            out(3)
        ).Default(
            out(None)
        )


if __name__ == "__main__":
    u = FsmExample()
    print(toRtl(u))
