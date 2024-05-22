#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal, HwIOClk
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override


class SimpleIfStatement(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        self.a = HwIOSignal()
        self.b = HwIOSignal()
        self.c = HwIOSignal()
        self.d = HwIOSignal()._m()

    @override
    def hwImpl(self):
        If(self.a,
           self.d(self.b),
        ).Elif(self.b,
           self.d(self.c)
        ).Else(
           self.d(0)
        )


class SimpleIfStatement2(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.a = HwIOSignal()
        self.b = HwIOSignal()
        self.c = HwIOSignal()
        self.d = HwIOSignal()._m()

    @override
    def hwImpl(self):
        r = self._reg("reg_d", def_val=0)

        If(self.a,
            If(self.b & self.c,
               r(1),
            ).Else(
               r(0)
            )
        )
        self.d(r)


class SimpleIfStatement2b(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.a = HwIOSignal()
        self.b = HwIOSignal()
        self.c = HwIOSignal()
        self.d = HwIOSignal()._m()

    @override
    def hwImpl(self):
        r = self._reg("reg_d", def_val=0)

        If(self.a & self.b,
            If(self.c,
               r(1),
            )
        ).Elif(self.c,
            r(0)
        )
        self.d(r)


class SimpleIfStatement2c(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.a = HwIOSignal()
        self.b = HwIOSignal()
        self.c = HwIOSignal()
        self.d = HwIOVectSignal(2)._m()

    @override
    def hwImpl(self):
        r = self._reg("reg_d", HBits(2), def_val=0)

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
    @override
    def hwImpl(self):
        If(self.a,
           self.d(0),
        ).Elif(self.b,
           self.d(0)
        ).Else(
           self.d(0)
        )


class SimpleIfStatementMergable(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        self.a = HwIOSignal()
        self.b = HwIOSignal()

        self.c = HwIOSignal()._m()
        self.d = HwIOSignal()._m()

    @override
    def hwImpl(self):
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


class SimpleIfStatementMergable1(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        self.a = HwIOSignal()
        self.b = HwIOSignal()

        self.c = HwIOSignal()._m()
        self.d = HwIOSignal()._m()
        self.e = HwIOSignal()

    @override
    def hwImpl(self):
        If(self.e,
            If(self.a,
                self.d(self.b),
            ),
            If(self.a,
                self.c(self.b),
            )
        )


class SimpleIfStatementMergable2(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        self.a = HwIOSignal()
        self.b = HwIOSignal()

        self.c = HwIOSignal()
        self.d = HwIOSignal()._m()
        self.e = HwIOSignal()._m()
        self.f = HwIOSignal()._m()

    @override
    def hwImpl(self):
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


class SimpleIfStatementPartialOverride(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        self.a = HwIOSignal()
        self.b = HwIOSignal()

        self.c = HwIOSignal()._m()

    @override
    def hwImpl(self):
        If(self.b,
            self.c(1),
            If(self.a,
                self.c(self.b),
            ),
        )

class SimpleIfStatementPartialOverrideNopVal(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        self.clk = HwIOClk()
        self.a = HwIOSignal()
        self.b = HwIOSignal()
        self.c = HwIOSignal()

        self.e = HwIOSignal()._m()

    @override
    def hwImpl(self):
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


class IfStatementPartiallyEnclosed(HwModule):
    """
    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        self.clk = HwIOClk()
        self.a = HwIOSignal()._m()
        self.b = HwIOSignal()._m()

        self.c = HwIOSignal()
        self.d = HwIOSignal()

    @override
    def hwImpl(self):
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
    from hwt.synth import to_rtl_str
    
    m = SimpleIfStatementPartialOverrideNopVal()
    print(to_rtl_str(m))
