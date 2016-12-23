#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal
from hwt.intfLvl import Unit
from hwtLib.samples.iLvl.simple import SimpleUnit


class SimpleSubunit(Unit):
    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        
        self.subunit0 = SimpleUnit()

    def _impl(self):
        u = self.subunit0
        u.a ** self.a
        self.b ** u.b
        

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleSubunit()))
