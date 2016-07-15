from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.amba import AxiStream_withoutSTRB
from hdl_toolkit.synthetisator.param import Param, evalParam
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import c, packedWidth, \
    packed, connectUnpacked
from hdl_toolkit.synthetisator.shortcuts import toRtl
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn

from hwtLib.mem.fifo import Fifo

class AxiSFifo(Unit):
    """
    Synchronous fifo for axi-stream interface. 
    """
    def __init__(self, axiIntfCls):
        """
        @param axiIntfCls: class of interface which should be used as interface of this unit
        """
        assert(issubclass(axiIntfCls, AxiStream_withoutSTRB))
        self.hsIntCls = axiIntfCls
        super().__init__()
        
    def _config(self):
        self.DEPTH = Param(0)
        self.hsIntCls._config(self)
        
    def _declr(self):
        addClkRstn(self)
        self.din = self.hsIntCls(isExtern=True)
        self.dout = self.hsIntCls(isExtern=True)
        
        self._shareAllParams()

        if evalParam(self.DEPTH).val > 0:
            self.fifo = Fifo()
            DW = packedWidth(self.din) - 2  # 2 for control (valid, ready)
            self.fifo.DATA_WIDTH.set(DW)
            self.fifo.DEPTH.set(self.DEPTH)
        
    def _impl(self):
        din = self.din
        dout = self.dout
        d = evalParam(self.DEPTH).val
        if d == 0:
            c(din, dout)
        else:
            propagateClkRstn(self)
            fifo = self.fifo
            
            # to fifo
            c(~fifo.din.wait, din.ready)
            c(packed(din, exclude=[din.valid, din.ready]), fifo.din.data)
            
            # from fifo
            c(~fifo.dout.wait, dout.valid)
            connectUnpacked(fifo.dout.data, dout, exclude=[dout.valid, dout.ready])
            
if __name__ == "__main__":
    u = AxiSFifo(AxiStream_withoutSTRB)
    u.DEPTH.set(4)
    
    print(toRtl(u))    
            
            
            
