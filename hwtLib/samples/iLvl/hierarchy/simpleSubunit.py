#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal
from hwt.intfLvl import Unit
from hwtLib.samples.iLvl.simple import SimpleUnit


class SimpleSubunit(Unit):
    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        
        # there we instantiate our subunit and register it by assigning to property of self 
        # it can be done in done in _impl as well,
        # but if you do it there it offers more possibilities for parallelization
        # and any configuration for unit has to be made before registering in _impl
        self.subunit0 = SimpleUnit()

    def _impl(self):
        u = self.subunit0
        u.a ** self.a
        self.b ** u.b
        

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = SimpleSubunit()
    print(toRtl(u))
