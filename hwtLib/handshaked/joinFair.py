#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import And, If, Or, iterBits, ror
from hwt.hdlObjects.typeShortcuts import vecT
from hwtLib.handshaked.join import HandshakedJoin
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param, evalParam
from hwt.interfaces.std import VectSignal

def priorityOverriden(priorityReg, vldSignals, index):
    owr = []
    for i, (p, vld) in  enumerate(zip(iterBits(priorityReg), vldSignals)):
        if i != index:
            owr.append(p & vld)
        
    return And(*owr)

class HsJoinFairShare(HandshakedJoin):
    """
    Join input stream to single output stream
    inputs with lower number has higher priority
    
    Priority is changing every clock 
    If prioritized input is not sending valid data, 
    input with lowest index and valid is used
    
    combinational
    """
    def _config(self):
        HandshakedJoin._config(self)
        self.EXPORT_SELECTED = Param(True)
    
    def _declr(self):
        HandshakedJoin._declr(self)
        addClkRstn(self)
        if evalParam(self.EXPORT_SELECTED).val:
            self.selectedOneHot = VectSignal(self.INPUTS)
        
    def _impl(self):
        rd = self.getRd
        vld = self.getVld
        data = self.getData
        dout = self.dataOut
        EXPORT_SELECTED = evalParam(self.EXPORT_SELECTED).val
        
        priority = self._reg("priority", vecT(self.INPUTS), defVal=1)
        
        vldSignals = list(map(vld, self.dataIn))  
        
        outMuxTop = []
        for d in data(dout):
            outMuxTop.extend(d ** None)
        
        for i, din in enumerate(self.dataIn):
            priorityOverride = priorityOverriden(priority, vldSignals, i)  
            if i == 0:
                isSelected = ~priorityOverride 
            else:
                allHigherPriorNotVld = map(lambda x:~x, vldSignals[:i])
                isSelected = And(*allHigherPriorNotVld) | ~priorityOverride 
                
            rd(din) ** (isSelected & rd(dout))
            
            if EXPORT_SELECTED:
                self.selectedOneHot[i] ** isSelected 
            
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
