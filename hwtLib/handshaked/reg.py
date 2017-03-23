#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import addClkRstn
from hwt.code import If, c
from hwtLib.handshaked.compBase import HandshakedCompBase 
from hwt.synthesizer.param import Param, evalParam
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName


class HandshakedReg(HandshakedCompBase):
    """
    Register for Handshaked interface
    """
    def _config(self):
        HandshakedCompBase._config(self)
        self.LATENCY = Param(1)
        self.DELAY = Param(0)
        
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = self.intfCls()
            self.dataOut = self.intfCls()

    def _impl_latency(self, inVld, inRd, inData, outVld, outRd, prefix):
        isOccupied = self._reg(prefix + "isOccupied", defVal=0)
        regs_we = self._sig(prefix + 'reg_we')
        
        outData = []
        for iin in inData:
            r = self._reg(prefix + 'reg_' + iin._name, iin._dtype)
            
            If(regs_we,
                r ** iin
            )
            outData.append(r)
    
        If(isOccupied,
            If(outRd & ~inVld,
                isOccupied ** 0
            )
        ).Else(
            If(inVld,
               isOccupied ** 1
            )
        )
        
        If(isOccupied,
           c(outRd, inRd),
           outVld ** 1,
           regs_we ** (inVld & outRd)
        ).Else(
           inRd ** 1,
           outVld ** 0,
           regs_we ** inVld
        )
        return outData

    def _implLatencyAndDelay(self, inVld, inRd, inData, outVld, outRd, prefix):
        wordLoaded = self._reg("wordLoaded", defVal=0)
        If(wordLoaded,
           wordLoaded ** ~outRd
        ).Else(
           wordLoaded ** inVld
        )
        
        outData = []
        for iin in inData:
            r = self._reg('reg_' + getSignalName(iin), iin._dtype)
            If(~wordLoaded,
               r ** iin
            )
            outData.append(r)
        
        
        inRd ** ~wordLoaded
        outVld ** wordLoaded
        
        return outData
    
    def _impl(self):
        LATENCY = evalParam(self.LATENCY).val
        DELAY = evalParam(self.DELAY).val
        
        vld = self.getVld
        rd = self.getRd
        data = self.getData
        
        Out = self.dataOut
        In = self.dataIn
        if LATENCY == 1 and DELAY == 0:
            outData = self._impl_latency(vld(In), rd(In), data(In), vld(Out), rd(Out), "latency1_")
        elif LATENCY == 2 and DELAY == 1:
            latency1_vld = self._sig("latency1_vld")
            latency1_rd = self._sig("latency1_rd")
            outData = self._impl_latency(vld(In), rd(In), data(In), latency1_vld, latency1_rd, "latency1_")
            outData = self._implLatencyAndDelay(latency1_vld, latency1_rd, outData, vld(Out), rd(Out), "latency2_delay1_")
        else:
            raise NotImplementedError(LATENCY, DELAY)
        
        for ds, dm in zip(data(Out), outData):
            ds ** dm

if __name__ == "__main__":
    from hwt.interfaces.std import Handshaked
    from hwt.synthesizer.shortcuts import toRtl
    u = HandshakedReg(Handshaked)
    
    print(toRtl(u))
