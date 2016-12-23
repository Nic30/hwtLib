#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT, hInt
from hwt.interfaces.std import Signal
from hwt.intfLvl import Param, Unit


class SimpleUnit4(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(16)
        
    def _declr(self):
        # create vector type of width DATA_WIDTH / 8
        # by default vector does not have any sign, if it is used in arithmetic
        # operations it is automaticaly to unsigned 
        dtype = vecT(self.DATA_WIDTH // hInt(8))
        # create interfaces with datatype 
        # note that width of type is expression even in hdl
        # this simplifies orientation in generated code
        self.a = Signal(dtype=dtype)
        self.b = Signal(dtype=dtype)
        
    def _impl(self):
        self.a ** self.b


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleUnit4()))
