from hdl_toolkit.intfLvl import Param, c
from hdl_toolkit.synthetisator.param import evalParam
from hdl_toolkit.interfaces.std import Handshaked
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import packedWidth, packed,\
    connectUnpacked

from hwtLib.mem.fifo import Fifo
from hwtLib.handshaked.compBase import HandshakedCompBase

class HandshakedFifo(HandshakedCompBase):
    def _config(self):
        self.DEPTH = Param(0) 
        super()._config()
        
    def _declr(self):
        addClkRstn(self)
        with self._asExtern(), self._paramsShared():
            self.dataIn = self.intCls()
            self.dataOut = self.intCls()

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
            c(packed(din, fifo.dataIn.data, 
                     exclude=[vld(din), rd(din)]))
            
            # from fifo
            c(~fifo.dataOut.wait, vld(dout))
            connectUnpacked(fifo.dataOut.data, dout, 
                            exclude=[vld(dout),rd(dout)])
        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(HandshakedFifo(Handshaked)))