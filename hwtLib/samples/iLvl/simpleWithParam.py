#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.intfLvl import Param, Unit


class SimpleUnitWithParam(Unit):
    """
    Simple parametrized unit.
    """
    def _config(self):
        # declaration of parameter DATA_WIDTH with default value 8
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        # vecT is shortcut for vector type first parameter is width, second optional is signed flag
        dt = vecT(self.DATA_WIDTH)
        # dt is now vector with width specified by parameter DATA_WIDTH
        # it means it is 8bit width 
        # we specify datatype for every signal
        self.a = Signal(dtype=dt)
        self.b = Signal(dtype=dt)
        
    def _impl(self):
        self.b ** self.a
        
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleUnitWithParam))
