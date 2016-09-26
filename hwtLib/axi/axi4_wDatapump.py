from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn, log2ceil
from hwtLib.interfaces.amba import Axi4_w, Axi4_addr, AxiStream, Axi4_b
from hwtLib.interfaces.amba_constants import BURST_INCR, CACHE_DEFAULT, LOCK_DEFAULT, PROT_DEFAULT, QOS_DEFAULT, \
    BYTES_IN_TRANS, RESP_OKAY
from hwtLib.axi.axi4_rDatapump import AddrSizeHs
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.synthesizer.codeOps import connect, If
from hdl_toolkit.bitmask import Bitmask

def axiHsAck(m, s):
    return m.valid & s.ready

class Axi4_wDatapump(Unit):
    """
    @ivar param MAX_TRANS_OVERLAP: max number of concurent transactios
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
                
        
    def useTransSplitting(self):
        return self.req.len._dtype.bit_length() > self.ar.len._dtype.bit_length()
    
    def getSizeAlignBits(self):
        return log2ceil(self.DATA_WIDTH // 8).val
    
    def getAxiLenMax(self):
        return Bitmask.mask(self.ar.len._dtype.bit_length())
    
    def getBurstAddrOffset(self):
        return (self.getAxiLenMax() + 1) << self.getSizeAlignBits()
    
     
    def axiAwHandler(self, enable):
        req = self.req
        aw = self.aw
        
        aw.id ** self.DEFAULT_ID
        aw.burst ** BURST_INCR
        aw.cache ** CACHE_DEFAULT
        aw.lock ** LOCK_DEFAULT
        aw.prot ** PROT_DEFAULT
        aw.qos ** QOS_DEFAULT
        aw.size ** BYTES_IN_TRANS(evalParam(self.DATA_WIDTH).val)

        if self.useTransSplitting():
            LEN_MAX = Bitmask.mask(aw.len._dtype.bit_length())
            
            lastReqDispatched = self._reg("lastReqDispatched", defVal=1)
            
            lenDebth = self._reg("lenDebth", req.len._dtype)
            rAddr = self._reg("r_addr", req.addr._dtype)
            
            If(lastReqDispatched,
               aw.addr ** req.addr,
               connect(req.len, aw.len, fit=True),
               aw.valid ** (enable & req.vld),
               rAddr ** (req.addr + self.getBurstAddrOffset()),
               lenDebth ** (req.len - LEN_MAX),
               If(enable & (req.len > LEN_MAX) & aw.ready & req.vld,
                  lastReqDispatched ** 1 
               )
            ).Else(
               aw.addr ** rAddr,
               connect(lenDebth, aw.len, fit=True),
               aw.valid ** enable,
               If(enable & aw.ready,
                  rAddr ** (rAddr + self.getBurstAddrOffset()),
                  lenDebth ** (lenDebth - LEN_MAX),
                  If(lenDebth <= LEN_MAX,
                     lastReqDispatched ** 1
                  )
               )
            )
            
            ack = aw.ready & ((lastReqDispatched & req.vld) | ~lastReqDispatched)
            
        else:
            aw.addr ** req.addr
            connect(req.len, aw.len, fit=True)
            aw.valid ** req.vld 
            req.rd ** aw.ready
            
            ack = aw.ready & req.vld
            
        return ack
    
    def axiWHandler(self, enable):
        w = self.w
        wIn = self.wIn

        w.id ** self.DEFAULT_ID
        w.data ** wIn.data
        w.strb ** wIn.strb
        
        if self.useTransSplitting():
            wordCntr = self._reg("wWordCntr", self.aw.len._dtype, 0)
            If(enable & axiHsAck(wIn, w),
               If(wIn.last,
                   wordCntr ** 0
               ).Else(
                   wordCntr ** (wordCntr + 1)
               )
            )
            
            w.last ** (wordCntr._eq(self.getAxiLenMax()) | wIn.last)
            w.valid ** (enable & wIn.valid)
            wIn.ready ** (enable & w.ready)

        else:
            w.last ** wIn.last
            w.valid ** (enable & wIn.valid)
            wIn.ready ** w.ready
            
    def axiBHandler(self, enable):
        wErrFlag = self._reg("wErrFlag", defVal=0)
        b = self.b
        If(enable & b.valid & (b.resp != RESP_OKAY),
           wErrFlag ** 1
        )

        self.wErrFlag * wErrFlag 
        b.ready ** enable
        
        ack = b.valid
        return ack
    
    def _impl(self):
        propagateClkRstn(self)
        
        self.axiWHandler()
