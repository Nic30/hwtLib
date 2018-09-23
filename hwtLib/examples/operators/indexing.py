#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import connect
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal
from hwt.synthesizer.unit import Unit


class SimpleIndexingSplit(Unit):
    """
    .. hwt-schematic::
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
    .. hwt-schematic::
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
    .. hwt-schematic::
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
    .. hwt-schematic::
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


class IndexingInernSplit(Unit):
    """
    .. hwt-schematic::
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
    .. hwt-schematic::
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

        connect(intern[0], self.c)
        connect(intern[1], self.d)


if __name__ == "__main__":  # alias python main function
    from hwt.synthesizer.utils import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(IndexingInernSplit()))
