#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.synthesizer.codeOps import connect
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit


class SimpleIndexingSplit(Unit):
    def _declr(self):
        self.a = Signal(dtype=vecT(2))
        self.b = Signal()
        self.c = Signal()
        
    def _impl(self):
        self.b ** self.a[0]
        self.c ** self.a[1]

class SimpleIndexingJoin(Unit):
    def _declr(self):
        self.a = Signal(dtype=vecT(2))
        self.b = Signal()
        self.c = Signal()
        
    def _impl(self):
        self.a[0] ** self.b
        self.a[1] ** self.c

class SimpleIndexingRangeJoin(Unit):
    def _declr(self):
        self.a = Signal(dtype=vecT(4))
        self.b = Signal(dtype=vecT(2))
        self.c = Signal(dtype=vecT(2))
        
    def _impl(self):
        self.a[2:0] ** self.b
        self.a[4:2] ** self.c 

class IndexingInernRangeSplit(Unit):
    def _declr(self):
        self.a = Signal(dtype=vecT(4))
        self.b = Signal(dtype=vecT(4))

    def _impl(self):
        internA = self._sig("internA", vecT(2))
        internB = self._sig("internB", vecT(2))
        
        internA ** self.a[2:]
        internB ** self.a[:2] 
        
        
        self.b[2:] ** internA
        self.b[:2] ** internB
        

class IndexingInernSplit(Unit):
    def _declr(self):
        self.a = Signal(dtype=vecT(2))
        self.b = Signal(dtype=vecT(2))
    
    def _impl(self):
        internA = self._sig("internA")
        internB = self._sig("internB")
        
        internA ** self.a[0]
        internB ** self.a[1]
        
        
        self.b[0] ** internA 
        self.b[1] ** internB
        
class IndexingInernJoin(Unit):
    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = Signal()

    def _impl(self):
        intern = self._sig("internSig", vecT(2))
        
        intern[0] ** self.a 
        intern[1] ** self.b
        
        
        connect(intern[0], self.c)
        connect(intern[1], self.d)
        



if __name__ == "__main__":  # alias python main function
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(IndexingInernSplit))
