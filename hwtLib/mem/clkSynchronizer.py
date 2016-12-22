#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.types.defs import BIT
from hwt.interfaces.std import Rst, Signal, Clk
from hwt.intfLvl import Unit


class ClkSynchronizer(Unit):
    """
    Signal synchronization between two clock domains
    http://www.sunburst-design.com/papers/CummingsSNUG2008Boston_CDC.pdf
    """
    
    def _config(self):
        self.DATA_TYP = BIT
        
    def _declr(self):
        self.rst = Rst()
        
        self.inData = Signal(dtype=self.DATA_TYP)
        self.inClk = Clk()
        
        self.outData = Signal(dtype=self.DATA_TYP)
        self.outClk = Clk()
        
        
    def _impl(self):
        def reg(name, clk):
            return self._cntx.sig(name, self.DATA_TYP, clk=clk, syncRst=self.rst, defVal=0)
        inReg = reg("inReg", self.inClk)
        outReg0 = reg("outReg0", self.outClk)
        outReg1 = reg("outReg1", self.outClk)
        
        
        inReg ** self.inData
        
        outReg0 ** inReg
        outReg1 ** outReg0
        self.outData ** outReg1
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(ClkSynchronizer))
