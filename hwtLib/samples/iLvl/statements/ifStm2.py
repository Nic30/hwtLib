#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.interfaces.std import Signal, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.intfLvl import Unit
from hwt.hdlObjects.typeShortcuts import vecT


class SimpleIfStatement2(Unit):
    def _declr(self):
        addClkRstn(self)
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = Signal()

    def _impl(self):
        r = self._reg("reg_d", defVal=0)

        If(self.c,
            If(self.a & self.b,
               r ** 1,
            ).Else(
               r ** 0
            )
        )
        self.d ** r


class SimpleIfStatement2b(Unit):
    def _declr(self):
        addClkRstn(self)
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = Signal()

    def _impl(self):
        r = self._reg("reg_d", defVal=0)

        If(self.a & self.b,
            If(self.c,
               r ** 1,
            )
        ).Elif(self.c,
            r ** 0
        )
        self.d ** r


class SimpleIfStatement2c(Unit):
    def _declr(self):
        addClkRstn(self)
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = VectSignal(2)

    def _impl(self):
        r = self._reg("reg_d", vecT(2), defVal=0)

        If(self.a & self.b,
            If(self.c,
               r ** 0,
            )
        ).Elif(self.c,
            r ** 1
        ).Else(
            r ** 2
        )
        self.d ** r

if __name__ == "__main__":  # alias python main function
    from hwt.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SimpleIfStatement2c()))
