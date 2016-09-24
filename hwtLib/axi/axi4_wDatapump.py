from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param
from hdl_toolkit.interfaces.utils import addClkRstn
from hwtLib.interfaces.amba import Axi4_w, Axi4_addr, AxiStream, Axi4_b
from hwtLib.axi.axi4_rDatapump import AddrSizeHs
from hdl_toolkit.interfaces.std import Signal, Handshaked
from hwtLib.handshaked.fifo import HandshakedFifo

class Axi4_wDatapump(Unit):
    """
    b channel is used only for collecting 
    """
    
    def _config(self):
        self.DEFAULT_ID = Param(0)
        self.MAX_TRANS_OVERLAP = Param(16)
        self.MAX_LEN = Param(4096 // 8 - 1)
        
        self.ID_WIDTH = Param(4)
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
    
        
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.aw = Axi4_addr()
                self.w = Axi4_w()
                self.b = Axi4_b()
                
                self.req = AddrSizeHs()
                self.wIn = AxiStream()
                
                self.wErrFlag = Signal()
                
        f = self.sizeRmFifo = HandshakedFifo(Handshaked)
        f.DATA_WIDTH.set(self.getSizeAlignBits())
        f.DEPTH.set(self.MAX_TRANS_OVERLAP)
                