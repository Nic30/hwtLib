#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Switch, If
from hwt.hdlObjects.types.enum import Enum
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit


class AxiSsof(Unit):
    """
    Start of frame detector for axi stream
    """
    def _declr(self):
        addClkRstn(self)
        
        self.ready = Signal()
        self.valid = Signal()
        self.last = Signal()
        self.sof = Signal()
        
    def listenOn(self, axi, dstReady):
        self.ready ** dstReady
        self.valid ** axi.valid
        self.last ** axi.last 
        

    def _impl(self):
        stT = Enum("stT", ["stSof", 'stIdle'])
        st = self._reg("st", stT, stT.stSof)
        
        # next state logic
        Switch(st)\
        .Case(stT.stSof,
            If(self.valid & self.ready & ~self.last,
               st ** stT.stIdle
            )
        ).Case(stT.stIdle,
            If(self.valid & self.ready & self.last,
               st ** stT.stSof
            )
        )
                
        self.sof ** st._eq(stT.stSof)

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiSsof()
    print(toRtl(u))
