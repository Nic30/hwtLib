#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override


class SimpleIndexingSplit(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(2)
        self.b = HwIOSignal()._m()
        self.c = HwIOSignal()._m()

    @override
    def hwImpl(self):
        self.b(self.a[0])
        self.c(self.a[1])


class SimpleIndexingJoin(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(2)._m()
        self.b = HwIOSignal()
        self.c = HwIOSignal()

    @override
    def hwImpl(self):
        self.a[0](self.b)
        self.a[1](self.c)


class SimpleIndexingRangeJoin(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(4)._m()
        self.b = HwIOVectSignal(2)
        self.c = HwIOVectSignal(2)

    @override
    def hwImpl(self):
        self.a[2:0](self.b)
        self.a[4:2](self.c)
        assert len(self.a._sig._rtlDrivers) == 2


class IndexingInernRangeSplit(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(4)
        self.b = HwIOVectSignal(4)._m()

    @override
    def hwImpl(self):
        internA = self._sig("internA", HBits(2))
        internB = self._sig("internB", HBits(2))

        internA(self.a[2:])
        internB(self.a[:2])

        self.b[2:](internA)
        self.b[:2](internB)


class IndexingInternSplit(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(2)
        self.b = HwIOVectSignal(2)._m()

    @override
    def hwImpl(self):
        internA = self._sig("internA")
        internB = self._sig("internB")

        internA(self.a[0])
        internB(self.a[1])

        self.b[0](internA)
        self.b[1](internB)


class IndexingInernJoin(HwModule):
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
        intern = self._sig("internSig", HBits(2))

        intern[0](self.a)
        intern[1](self.b)

        self.c(intern[0])
        self.d(intern[1])


class AssignmentToRegIndex(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.a = HwIOVectSignal(2)
        self.b = HwIOVectSignal(2)._m()

    @override
    def hwImpl(self):
        intern = self._reg("internReg", HBits(2))

        intern[0](intern[0] & self.a[0])
        intern[1](intern[1] | self.a[1])

        self.b(intern)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = AssignmentToRegIndex()
    print(to_rtl_str(m))
