#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.intfLvl import Unit
from hwtLib.handshaked.builder import HsBuilder


class HandshakedSimple(Unit):
    def _declr(self):
        addClkRstn(self)
        self.a = Handshaked()
        self.b = Handshaked()
        
    def _impl(self):
        b = HsBuilder(self, self.a)

        b.reg()
        b.fifo(16)
        b.reg()
        
        self.b ** b.end 
        

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(HandshakedSimple))
