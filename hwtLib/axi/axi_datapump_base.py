from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hwtLib.interfaces.amba import Axi4_addr
from hdl_toolkit.synthesizer.param import Param, evalParam
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil
from hdl_toolkit.interfaces.agents.handshaked import HandshakedAgent
from hdl_toolkit.interfaces.std import Handshaked, VectSignal, HandshakeSync
from hdl_toolkit.bitmask import mask
from hwtLib.interfaces.amba_constants import BURST_INCR, CACHE_DEFAULT,\
    LOCK_DEFAULT, PROT_DEFAULT, QOS_DEFAULT, BYTES_IN_TRANS

class AddrSizeHsAgent(HandshakedAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.read
        
        _id = r(intf.id)
        addr = r(intf.addr)
        _len = r(intf.len)
        rem = r(intf.rem)
        
        return (_id, addr, _len, rem)

    def mkReq(self, addr, _len, rem=0, _id=0):
        return (_id, addr, _len, rem)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.w
        
        if data is None:
            data = [None for _ in range(4)]

        _id, addr, _len, rem = data
        
        w(_id, intf.id)
        w(addr, intf.addr)
        w(_len, intf.len)
        w(rem, intf.rem)
    
class AddrSizeHs(Handshaked):
    def _config(self):
        self.ID_WIDTH = Param(4)
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.MAX_LEN = Param(4096 // 8 - 1)
    
    def _declr(self):
        self.id = VectSignal(self.ID_WIDTH)
        
        self.addr = VectSignal(self.ADDR_WIDTH)
        #  len is number of words -1
        self.len = VectSignal(log2ceil(self.MAX_LEN))
        
        # rem is number of bits in last word which is valid - 1
        self.rem = VectSignal(log2ceil(self.DATA_WIDTH // 8))

        HandshakeSync._declr(self)
    
    def _getSimAgent(self):
        return AddrSizeHsAgent

class Axi_datapumpBase(Unit):
    """
    @ivar param MAX_TRANS_OVERLAP: max number of concurrent transactions
 
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
        if self._addrHasUser:
            self.ADDR_USER_VAL = Param(0)
    
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                # address channel to axi
                self.a = self._axiAddrCls()
                self.a.LOCK_WIDTH = 2 # because all masters have it
                # user requests
                self.req = AddrSizeHs()
                
    def getSizeAlignBits(self):
        return log2ceil(self.DATA_WIDTH // 8).val
    
    def useTransSplitting(self):
        return self.req.len._dtype.bit_length() > self.a.len._dtype.bit_length()
    
    def getBurstAddrOffset(self):
        return (self.getAxiLenMax() + 1) << self.getSizeAlignBits()

    def getAxiLenMax(self):
        return mask(self.a.len._dtype.bit_length())
    
    def axiAddrDefaults(self):
        a = self.a
        a.burst ** BURST_INCR
        a.cache ** CACHE_DEFAULT
        a.lock ** LOCK_DEFAULT
        a.prot ** PROT_DEFAULT
        a.qos ** QOS_DEFAULT
        a.size ** BYTES_IN_TRANS(evalParam(self.DATA_WIDTH).val)
        if self._addrHasUser:
            a.user ** self.ADDR_USER_VAL