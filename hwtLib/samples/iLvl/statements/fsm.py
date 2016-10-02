#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.synthesizer.codeOps import FsmBuilder, Switch, If
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.shortcuts import toRtl


class FsmExample(Unit):
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.a = Signal()
            self.b = Signal()
            self.dout = Signal(dtype=vecT(3))
            
            
    def _impl(self):
        stT = Enum("st_t", ["a", "b", "aAndB"])
        
        a = self.a
        b = self.b
        out = self.dout
        
        st = FsmBuilder(self, stT)\
        .Trans(stT.a,
            (a & b, stT.aAndB),
            (b, stT.b)
        ).Trans(stT.b,
            (a & b, stT.aAndB),
            (a, stT.a)
        ).Trans(stT.aAndB,
            (a & ~b, stT.a),
            (~a & b, stT.b),
        ).stateReg
        
        
        Switch(st)\
        .Case(stT.a,
              out ** 1
        ).Case(stT.b,
              out ** 2
        ).Case(stT.aAndB,
              out ** 3
        )
        
class HadrcodedFsmExample(FsmExample):
    def _impl(self):
        a = self.a
        b = self.b
        out = self.dout
        
        st = self._reg("st", vecT(3), 1) 
        
        If(st._eq(1),
            If(a & b,
                st ** 3
            ).Elif(b,
                st ** 2
            ).Else(
                st ** st
            )
        ).Elif(st._eq(2),
            If(a & b,
               st ** 3
            ).Elif(a,
                st ** 1
            ).Else(
                st ** st
            )
        ).Elif(st._eq(3),
            If(a & ~b,
               st ** 1
            ).Elif(~a & b,
                st ** 2
            ).Else(
                st ** st
            )
        ).Else(
            st ** 1
        )
        
        
        Switch(st)\
        .Case(1,
            out ** 1
        ).Case(2,
            out ** 2
        ).Case(3,
            out ** 3
        ).Default(
            out ** None
        )
        
    
            
if __name__ == "__main__":
    u = FsmExample()
    print(toRtl(u))
