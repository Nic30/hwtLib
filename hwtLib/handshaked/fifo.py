#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hdl_toolkit.interfaces.std import VectSignal
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn, log2ceil
from hdl_toolkit.intfLvl import Param
from hdl_toolkit.synthesizer.codeOps import packedWidth, packed, \
    connectUnpacked, If, connect
from hdl_toolkit.synthesizer.param import evalParam
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.mem.fifo import Fifo


class HandshakedFifo(HandshakedCompBase):
    """
    Fifo for handshaked interfaces
    """
    _regCls = HandshakedReg
    
    def _config(self):
        self.DEPTH = Param(0)
        self.LATENCY = Param(1)
        self.EXPORT_SIZE = Param(False)
        super()._config()
        
    def _declr(self):
        with self._paramsShared():
            addClkRstn(self)
            self.dataIn = self.intfCls()
            self.dataOut = self.intfCls()

        f = self.fifo = Fifo()
        DW = packedWidth(self.dataIn) - 2  # 2 for control (valid, ready)
        f.DATA_WIDTH.set(DW)
        f.DEPTH.set(self.DEPTH - 1)  # because there is an extra register
        f.LATENCY.set(self.LATENCY)
        f.EXPORT_SIZE.set(self.EXPORT_SIZE)
        
        if evalParam(self.EXPORT_SIZE).val:
            self.size = VectSignal(log2ceil(self.DEPTH + 1 + 1), signed=False) 
    
        #if evalParam(self.LATENCY).val == 1:
        #    with self._paramsShared(): 
        #        self.outReg = self._regCls(self.intfCls)
          
                
    def _impl(self):
        din = self.dataIn
        rd = self.getRd
        vld = self.getVld

        propagateClkRstn(self)
        fifo = self.fifo
        
        #if evalParam(self.LATENCY).val == 1:
        #    out = self.outReg.dataIn
        #    self.dataOut ** self.outReg.dataOut
        #else:
        out = self.dataOut
        
        # to fifo
        wr_en = ~fifo.dataIn.wait
        rd(din) **  wr_en
        fifo.dataIn.data ** packed(din, exclude=[vld(din), rd(din)])
        fifo.dataIn.en ** (vld(din) & wr_en)
        
        
        # from fifo
        out_vld = self._reg("out_vld", defVal=0)
        vld(out) ** out_vld
        connectUnpacked(fifo.dataOut.data, out,
                        exclude=[vld(out), rd(out)])
        fifo.dataOut.en ** ((rd(out) | ~out_vld) & ~fifo.dataOut.wait)
        If(rd(out) | ~out_vld,
           out_vld ** (~fifo.dataOut.wait) 
        )
        
        if evalParam(self.EXPORT_SIZE).val:
            sizeTmp = self._sig("sizeTmp", self.size._dtype)
            connect(fifo.size, sizeTmp, fit=True)
            
            If(out_vld,
               self.size ** (sizeTmp + 1)
            ).Else(
               connect(fifo.size, self.size, fit=True)
            )
    
        
        
if __name__ == "__main__":
    from hdl_toolkit.interfaces.std import Handshaked
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = HandshakedFifo(Handshaked)
    u.DEPTH.set(8)
    u.DATA_WIDTH.set(4)
    u.EXPORT_SIZE.set(True)
    print(toRtl(u))
