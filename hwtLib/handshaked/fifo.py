from hdl_toolkit.interfaces.std import Handshaked
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn
from hdl_toolkit.intfLvl import Param, c
from hdl_toolkit.synthesizer.codeOps import packedWidth, packed, \
    connectUnpacked
from hdl_toolkit.synthesizer.param import evalParam
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.mem.fifo import Fifo


class HandshakedFifo(HandshakedCompBase):
    def _config(self):
        self.DEPTH = Param(0) 
        super()._config()
        
    def _declr(self):
        with self._asExtern(), self._paramsShared():
            addClkRstn(self)
            self.dataIn = self.intfCls()
            self.dataOut = self.intfCls()

        if evalParam(self.DEPTH).val > 0:
            self.fifo = Fifo()
            DW = packedWidth(self.dataIn) - 2  # 2 for control (valid, ready)
            self.fifo.DATA_WIDTH.set(DW)
            self.fifo.DEPTH.set(self.DEPTH)
        
    def _impl(self):
        din = self.dataIn
        dout = self.dataOut
        rd= self.getRd
        vld = self.getVld
        d = evalParam(self.DEPTH).val

        if d == 0:
            c(din, dout)
        else:
            propagateClkRstn(self)
            fifo = self.fifo
            
            # to fifo
            c(~fifo.dataIn.wait, rd(din))
            c(packed(din, exclude=[vld(din), rd(din)]),
               fifo.dataIn.data)
            c(vld(din) & ~fifo.dataIn.wait, fifo.dataIn.en)
            
            
            # from fifo
            c(~fifo.dataOut.wait, vld(dout))
            connectUnpacked(fifo.dataOut.data, dout, 
                            exclude=[vld(dout),rd(dout)])
            c(rd(dout) & ~fifo.dataOut.wait, fifo.dataOut.en)
        
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = HandshakedFifo(Handshaked)
    u.DEPTH.set(2)
    print(toRtl(u))