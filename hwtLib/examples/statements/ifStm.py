#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal, Clk
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit


class SimpleIfStatement(Unit):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = Signal()._m()

    def _impl(self):
        If(self.a,
           self.d(self.b),
        ).Elif(self.b,
           self.d(self.c)
        ).Else(
           self.d(0)
        )


class SimpleIfStatement2(Unit):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        addClkRstn(self)
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = Signal()._m()

    def _impl(self):
        r = self._reg("reg_d", def_val=0)

        If(self.a,
            If(self.b & self.c,
               r(1),
            ).Else(
               r(0)
            )
        )
        self.d(r)


class SimpleIfStatement2b(Unit):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        addClkRstn(self)
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = Signal()._m()

    def _impl(self):
        r = self._reg("reg_d", def_val=0)

        If(self.a & self.b,
            If(self.c,
               r(1),
            )
        ).Elif(self.c,
            r(0)
        )
        self.d(r)


class SimpleIfStatement2c(Unit):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        addClkRstn(self)
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = VectSignal(2)._m()

    def _impl(self):
        r = self._reg("reg_d", Bits(2), def_val=0)

        If(self.a & self.b,
            If(self.c,
               r(0),
            )
        ).Elif(self.c,
            r(1)
        ).Else(
            r(2)
        )
        self.d(r)


class SimpleIfStatement3(SimpleIfStatement):
    """
    .. hwt-autodoc::
    """
    def _impl(self):
        If(self.a,
           self.d(0),
        ).Elif(self.b,
           self.d(0)
        ).Else(
           self.d(0)
        )


class SimpleIfStatementMergable(Unit):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.a = Signal()
        self.b = Signal()

        self.c = Signal()._m()
        self.d = Signal()._m()

    def _impl(self):
        If(self.a,
           self.d(self.b),
        ).Else(
           self.d(0)
        )

        If(self.a,
            self.c(self.b),
        ).Else(
           self.c(0)
        )


class SimpleIfStatementMergable1(Unit):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.a = Signal()
        self.b = Signal()

        self.c = Signal()._m()
        self.d = Signal()._m()
        self.e = Signal()

    def _impl(self):
        If(self.e,
            If(self.a,
                self.d(self.b),
            ),
            If(self.a,
                self.c(self.b),
            )
        )


class SimpleIfStatementMergable2(Unit):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.a = Signal()
        self.b = Signal()

        self.c = Signal()
        self.d = Signal()._m()
        self.e = Signal()._m()
        self.f = Signal()._m()

    def _impl(self):
        If(self.a,
            self.d(self.b),
            # this two if statements will be merged together
            If(self.b,
               self.e(self.c)
            ),
            If(self.b,
               self.f(0)
            )
        ).Else(
           self.d(0)
        )


class SimpleIfStatementPartialOverride(Unit):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.a = Signal()
        self.b = Signal()

        self.c = Signal()._m()

    def _impl(self):
        If(self.b,
            self.c(1),
            If(self.a,
                self.c(self.b),
            ),
        )

class SimpleIfStatementPartialOverrideNopVal(Unit):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.clk = Clk()
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()

        self.e = Signal()._m()

    def _impl(self):
        d = self._reg("d")

        If(self.a,
            If(self.b,
                d(1),
            ),
            If(self.c,
                d(0),
            ),
        )
        self.e(d)


class IfStatementPartiallyEnclosed(Unit):
    """
    .. hwt-autodoc::
    """
    def _declr(self):
        self.clk = Clk()
        self.a = Signal()._m()
        self.b = Signal()._m()

        self.c = Signal()
        self.d = Signal()

    def _impl(self):
        a = self._reg("a_reg")
        b = self._reg("b_reg")

        If(self.c,
            a(1),
            b(1),
        ).Elif(self.d,
            a(0)
        ).Else(
            a(1),
            b(1),
        )
        self.a(a)
        self.b(b)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = SimpleIfStatementPartialOverrideNopVal()
    print(to_rtl_str(u))
