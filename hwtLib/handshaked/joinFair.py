#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.synthesizer.codeOps import And, If, Or, iterBits, ror
from hwt.hdlObjects.typeShortcuts import vecT
from hwtLib.handshaked.join import HandshakedJoin


class HsJoinFairShare(HandshakedJoin):
    """
    Join input stream to single output stream
    inputs with lower number has higher priority
    
    Priority is changing every clock 
    If prioritized input is not sending valid data, 
    input with lowest index and valid is used
    
    combinational
    """
    def priorityOverriden(self, priority, vldSignals, index):
        owr = []
        for i, (p, vld) in  enumerate(zip(iterBits(priority), vldSignals)):
            if i != index:
                owr.append(p & vld)
            
        return And(*owr)
        
    def _impl(self):
        rd = self.getRd
        vld = self.getVld
        data = self.getData
        dout = self.dataOut
        
        priority = self._reg("priority", vecT(self.INPUTS), defVal=1)
        
        vldSignals = list(map(vld, self.dataIn))  
        
        outMuxTop = []
        for d in data(dout):
            outMuxTop.extend(d ** None)
        
        for i, din in enumerate(self.dataIn):
            priorityOverride = self.priorityOverriden(priority, vldSignals, i)  
            # dataIn.rd
            allLowerPriorNotReady = map(lambda x:~x, vldSignals[:i])
            rd(din) ** (And(rd(dout), *allLowerPriorNotReady) & ~priorityOverride)
            
            # data out mux
            dataConnectExpr = []
            for _din, _dout in zip(data(din), data(dout)):
                dataConnectExpr.extend(_dout ** _din)
           
            outMuxTop = If(vld(din) & ~priorityOverride,
                dataConnectExpr
            ).Else(
                outMuxTop
            )
        priority ** ror(priority, 1)
            
        vld(dout) ** Or(*vldSignals)
                
        
if __name__ == "__main__":
    from hwt.interfaces.std import Handshaked
    from hwt.synthesizer.shortcuts import toRtl
    u = HsJoinFairShare(Handshaked)
    print(toRtl(u))
