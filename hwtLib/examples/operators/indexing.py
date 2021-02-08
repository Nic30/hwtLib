#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal
from hwt.synthesizer.unit import Unit
from hwt.interfaces.utils import addClkRstn


class SimpleIndexingSplit(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.a = VectSignal(2)
        self.b = Signal()._m()
        self.c = Signal()._m()

    def _impl(self):
        self.b(self.a[0])
        self.c(self.a[1])


class SimpleIndexingJoin(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.a = VectSignal(2)._m()
        self.b = Signal()
        self.c = Signal()

    def _impl(self):
        self.a[0](self.b)
        self.a[1](self.c)


class SimpleIndexingRangeJoin(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.a = VectSignal(4)._m()
        self.b = VectSignal(2)
        self.c = VectSignal(2)

    def _impl(self):
        self.a[2:0](self.b)
        self.a[4:2](self.c)
        assert len(self.a._sig.drivers) == 2


class IndexingInernRangeSplit(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.a = VectSignal(4)
        self.b = VectSignal(4)._m()

    def _impl(self):
        internA = self._sig("internA", Bits(2))
        internB = self._sig("internB", Bits(2))

        internA(self.a[2:])
        internB(self.a[:2])

        self.b[2:](internA)
        self.b[:2](internB)


class IndexingInternSplit(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.a = VectSignal(2)
        self.b = VectSignal(2)._m()

    def _impl(self):
        internA = self._sig("internA")
        internB = self._sig("internB")

        internA(self.a[0])
        internB(self.a[1])

        self.b[0](internA)
        self.b[1](internB)


class IndexingInernJoin(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()._m()
        self.d = Signal()._m()

    def _impl(self):
        intern = self._sig("internSig", Bits(2))

        intern[0](self.a)
        intern[1](self.b)

        self.c(intern[0])
        self.d(intern[1])


class AssignmentToRegIndex(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        addClkRstn(self)
        self.a = VectSignal(2)
        self.b = VectSignal(2)._m()

    def _impl(self):
        intern = self._reg("internReg", Bits(2))

        intern[0](intern[0] & self.a[0])
        intern[1](intern[1] | self.a[1])

        self.b(intern)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = AssignmentToRegIndex()
    print(to_rtl_str(u))
