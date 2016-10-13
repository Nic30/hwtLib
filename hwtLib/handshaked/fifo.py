#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hdl_toolkit.interfaces.std import Handshaked, VectSignal
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn, log2ceil
from hdl_toolkit.intfLvl import Param
from hdl_toolkit.synthesizer.codeOps import packedWidth, packed, \
    connectUnpacked
from hdl_toolkit.synthesizer.param import evalParam
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.mem.fifo import Fifo


class HandshakedFifo(HandshakedCompBase):
    def _config(self):
        self.DEPTH = Param(0)
        self.LATENCY = Param(1)
        self.EXPORT_SIZE = Param(False)
        super()._config()
        
    def _declr(self):
        with self._asExtern(), self._paramsShared():
            addClkRstn(self)
            self.dataIn = self.intfCls()
            self.dataOut = self.intfCls()

        if evalParam(self.DEPTH).val > 0:
            f = self.fifo = Fifo()
            DW = packedWidth(self.dataIn) - 2  # 2 for control (valid, ready)
            f.DATA_WIDTH.set(DW)
            f.DEPTH.set(self.DEPTH)
            f.LATENCY.set(self.LATENCY)
            f.EXPORT_SIZE.set(self.EXPORT_SIZE)
            
            if evalParam(self.EXPORT_SIZE).val:
                with self._asExtern():
                    self.size = VectSignal(log2ceil(self.DEPTH), signed=False) 
                
    def _impl(self):
        din = self.dataIn
        dout = self.dataOut
        rd = self.getRd
        vld = self.getVld
        d = evalParam(self.DEPTH).val

        if d == 0:
            din ** dout
        else:
            propagateClkRstn(self)
            fifo = self.fifo
            
            # to fifo
            rd(din) ** ~fifo.dataIn.wait 
            fifo.dataIn.data ** packed(din, exclude=[vld(din), rd(din)])
            fifo.dataIn.en ** (vld(din) & ~fifo.dataIn.wait)
            
            
            # from fifo
            vld(dout) ** ~fifo.dataOut.wait
            connectUnpacked(fifo.dataOut.data, dout,
                            exclude=[vld(dout), rd(dout)])
            fifo.dataOut.en ** (rd(dout) & ~fifo.dataOut.wait)
            
            if evalParam(self.EXPORT_SIZE).val:
                self.size ** fifo.size
        
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = HandshakedFifo(Handshaked)
    u.DEPTH.set(2)
    print(toRtl(u))
