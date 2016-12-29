#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.code import If
from hwtLib.handshaked.compBase import HandshakedCompBase 
from hwtLib.handshaked.reg import HandshakedReg

# [TODO] there should be class of handshaked reg with 
#        parametrizable delay and latency
class HandshakedReg2(HandshakedCompBase):
    regCls = HandshakedReg
    """
    Register for Handshaked interface with latency of 2
    
    in->r0->r1->out
    
    two sets of registers
    in.rd = r0 or second set is invalid
    out.vld = r1 is vld
    
    mv r0, r1 if  ~r1vld | out.rd
    
    invalidate r1 if out.rd
    
    LATENCY=2
    DELAY=1
    """
    
    
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = self.intfCls()
            self.dataOut = self.intfCls()
            
            self.r0 = self.regCls(self.intfCls)
            
    def _impl(self):
        vld = self.getVld
        rd = self.getRd
        out = self.dataOut
        r0 = self.r0
        
        propagateClkRstn(self)
        r0.dataIn ** self.dataIn
        
        wordLoaded = self._reg("wordLoaded", defVal=0)
        If(wordLoaded,
           wordLoaded ** ~rd(out)
        ).Else(
           wordLoaded ** vld(r0.dataOut)
        )
        
        # r0rd, r0vld =rd(r0.dataOut), vld(r0.dataOut)
        # c(r0.dataOut, self.dataOut, exclude=[r0rd, r0vld])
        for iin, iout in zip(self.getData(r0.dataOut), self.getData(self.dataOut)):
            assert not iin._interfaces  # has not subintefraces (Not implemented)
            
            r = self._reg('reg_' + iin._name, iin._dtype)
            
            If(~wordLoaded,
               r ** iin
            )
            
            iout ** r
        
        
        rd(r0.dataOut) ** ~wordLoaded
        vld(out) ** wordLoaded
       
        
        
if __name__ == "__main__":
    from hwt.interfaces.std import Handshaked
    from hwt.synthesizer.shortcuts import toRtl
    u = HandshakedReg2(Handshaked)
    
    print(toRtl(u))
