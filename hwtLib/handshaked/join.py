#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import And, If, Or
from hwt.intfLvl import Param
from hwtLib.handshaked.compBase import HandshakedCompBase


class HandshakedJoin(HandshakedCompBase):
    """
    Join input stream to single output stream
    inputs with lower number has higher priority
    
    combinational
    """
    def _config(self):
        self.INPUTS = Param(2)
        super()._config()
        
    def _declr(self):
        with self._paramsShared():
            self.dataIn = self.intfCls(multipliedBy=self.INPUTS)
            self.dataOut = self.intfCls()

    def _impl(self):
        rd = self.getRd
        vld = self.getVld
        data = self.getData
        dout = self.dataOut
        
        vldSignals = list(map(vld, self.dataIn))  
        
        outMuxTop = []
        for d in data(dout):
            outMuxTop.extend(d ** None)
        
        for i, din in reversed(list(enumerate(self.dataIn))):
            # dataIn.rd
            allLowerPriorNotReady =  map(lambda x:~x, vldSignals[:i])
            rd(din) ** (And(rd(dout), *allLowerPriorNotReady))
            
            # data out mux
            dataConnectExpr = []
            for _din, _dout in zip(data(din), data(dout)):
                dataConnectExpr.extend(_dout ** _din)
           
            outMuxTop = If(vld(din),
                dataConnectExpr
            ).Else(
                outMuxTop
            )
            
        vld(dout) ** Or(*vldSignals)
                
        
if __name__ == "__main__":
    from hwt.interfaces.std import Handshaked
    from hwt.synthesizer.shortcuts import toRtl
    u = HandshakedJoin(Handshaked)
    print(toRtl(u))
