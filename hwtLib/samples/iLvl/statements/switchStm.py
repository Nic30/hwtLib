#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.intfLvl import Unit
from hwt.code import Switch


class SwitchStmUnit(Unit):
    def _declr(self):
        self.sel = Signal(dtype=vecT(2))
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = Signal()
            
    def _impl(self):
        Switch(self.sel)\
        .Case(0,
            self.a ** self.b
        ).Case(1,
            self.a ** self.c
        ).Case(2,
            self.a ** self.d
        ).Default(
            self.a ** 0
        )
        

if __name__ == "__main__":  # alias python main function
    from hwt.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SwitchStmUnit))
