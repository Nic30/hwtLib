#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.hdlObjects.types.defs import BIT
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.interfaces.utils import addClkRst, propagateClkRst
from hdl_toolkit.intfLvl import Unit


class DReg(Unit):
    """
    Basic d flip flop
    @attention: using this unit is pointless because HWToolkit can automaticaly 
                generate such a register for any interface and datatype
    """
    def _declr(self):
        with self._asExtern():
            addClkRst(self)
    
            self.din = Signal(dtype=BIT)
            self.dout = Signal(dtype=BIT)
        
        
    def _impl(self):
        internReg = self._reg("internReg", BIT, defVal=False)        
        
        internReg ** self.din
        self.dout ** internReg 

class DoubleDReg(Unit):
    def _declr(self):
        DReg._declr(self)
        
        self.reg0 = DReg()
        self.reg1 = DReg()
    
    def _impl(self):
        propagateClkRst(self)
        
        self.reg0.din ** self.din
        self.reg1.din ** self.reg0.dout 
        self.dout ** self.reg1.dout 
    
        
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = DoubleDReg()
    print(toRtl(u))
