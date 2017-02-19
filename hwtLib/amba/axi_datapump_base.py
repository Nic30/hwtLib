from hwt.bitmask import mask
from hwt.code import log2ceil
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.amba.axi4 import Axi4_addr
from hwtLib.amba.constants import BURST_INCR, CACHE_DEFAULT, \
    LOCK_DEFAULT, PROT_DEFAULT, QOS_DEFAULT, BYTES_IN_TRANS


class Axi_datapumpBase(Unit):
    """
    @ivar param MAX_TRANS_OVERLAP: max number of concurrent transactions
    @ivar driver: interface which is used to drive this datapump (AxiRDatapumpIntf or AxiWDatapumpIntf)
    """
    def __init__(self, axiAddrCls=Axi4_addr):
        self._axiAddrCls = axiAddrCls
        a = axiAddrCls()
        self._addrHasUser = hasattr(a, "USER_WIDTH") 
        super().__init__()
    
    def _config(self):
        self.MAX_TRANS_OVERLAP = Param(16)
        self.MAX_LEN = Param(4096 // 8 - 1)
        
        self.ID_WIDTH = Param(4)
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.CACHE_VAL = Param(CACHE_DEFAULT)
        self.PROT_VAL = Param(PROT_DEFAULT)
        self.QOS_VAL = Param(QOS_DEFAULT)
        
        if self._addrHasUser:
            self.ADDR_USER_VAL = Param(0)
    
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            # address channel to axi
            self.a = self._axiAddrCls()
            self.a.LOCK_WIDTH = 2  # because all masters have it

                
    def getSizeAlignBits(self):
        return log2ceil(self.DATA_WIDTH // 8).val
    
    def useTransSplitting(self):
        return self.driver.req.len._dtype.bit_length() > self.a.len._dtype.bit_length()
    
    def getBurstAddrOffset(self):
        return (self.getAxiLenMax() + 1) << self.getSizeAlignBits()

    def getAxiLenMax(self):
        return mask(self.a.len._dtype.bit_length())
    
    def axiAddrDefaults(self):
        a = self.a
        a.burst ** BURST_INCR
        a.cache ** self.CACHE_VAL
        a.lock ** LOCK_DEFAULT
        a.prot ** self.PROT_VAL
        a.qos ** self.QOS_VAL
        a.size ** BYTES_IN_TRANS(evalParam(self.DATA_WIDTH).val // 8)
        if self._addrHasUser:
            a.user ** self.ADDR_USER_VAL
