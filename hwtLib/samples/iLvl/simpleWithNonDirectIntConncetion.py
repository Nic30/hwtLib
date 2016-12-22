#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal
from hwt.intfLvl import Unit


class SimpleWithNonDirectIntConncetion(Unit):
    """
    Example of fact that interfaces does not have to be only extern
    the can be used even for connection inside unit
    """
    
    def _declr(self):
        self.a = Signal()
        self.c = Signal()
        
    def _impl(self):
        self.b = Signal()

        self.b ** self.a
        self.c ** self.b

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleWithNonDirectIntConncetion()))
