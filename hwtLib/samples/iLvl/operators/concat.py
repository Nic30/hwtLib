#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.code import Concat
from hwt.synthesizer.interfaceLevel.unit import Unit


class SimpleConcat(Unit):
    def _declr(self):
        self.a0 = Signal()
        self.a1 = Signal()
        self.a2 = Signal()
        self.a3 = Signal()

        self.a_out = Signal(dtype=vecT(4))
    
    def _impl(self):
        self.a_out ** Concat(self.a3, self.a2, self.a1, self.a0)
        

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleConcat))
