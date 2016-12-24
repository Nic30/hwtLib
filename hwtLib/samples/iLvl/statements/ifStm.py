#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal
from hwt.intfLvl import Unit
from hwt.code import If


class SimpleIfStatement(Unit):
    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = Signal()
            
    def _impl(self):
        If(self.a,
           self.d ** self.b,
        ).Elif(self.b,
           self.d ** self.c  
        ).Else(
           self.d ** 0 
        )

if __name__ == "__main__":  # alias python main function
    from hwt.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SimpleIfStatement))
