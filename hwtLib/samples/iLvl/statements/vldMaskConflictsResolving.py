#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.synthesizer.codeOps import If
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit


class VldMaskConflictsResolving(Unit):
    """
    Example how invalid value of condition does not matter when it has no effect on result
    """
    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
    
    def _impl(self):
        a = self.a
        b = self.b
        c = self.c
        
        If(a,
            If(b,
              c ** 1   
            ).Else(
              c ** 0
            )   
        ).Else(
            If(b,
              c ** 1   
            ).Else(
              c ** 0
            )   
        )

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = VldMaskConflictsResolving()
    print(toRtl(u))