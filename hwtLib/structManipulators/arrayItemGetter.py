from hwt.code import log2ceil
from hwt.interfaces.std import Handshaked, VectSignal
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwt.synthesizer.vectorUtils import fitTo
from hwtLib.axi.axi_datapump_base import AddrSizeHs
from hwtLib.handshaked.streamNode import streamSync
from hwtLib.interfaces.amba import AxiStream_withId


class ArrayItemGetter(Unit):
    """
    Get specific item from array by index
    """
    def _config(self):
        self.ITEMS = Param(32)
        self.ITEM_SIZE_IN_WORDS = Param(1)
        self.ID = Param(0)
        self.ID_WIDTH = Param(4)
        self.DATA_WIDTH = Param(64)
        self.ADDR_WIDTH = Param(32)
         
    def _declr(self):
        # addr of start of array
        self.base = VectSignal(self.ADDR_WIDTH)
        
        # input index of item to get
        self.index = Handshaked()
        self.index.DATA_WIDTH.set(log2ceil(self.ITEMS))
        
        
        # output item from array
        self.item = Handshaked()
        self.item.DATA_WIDTH.set(self.DATA_WIDTH * self.ITEM_SIZE_IN_WORDS)
        
        with self._paramsShared():
            # interface for communication with datapump
            self.req = AddrSizeHs()
            self.req.MAX_LEN.set(self.ITEMS - 1)
            self.r = AxiStream_withId()
    
    def _impl(self):
        ITEM_SIZE_IN_WORDS = evalParam(self.ITEM_SIZE_IN_WORDS).val
        
        streamSync(masters=[self.index], slaves=[self.req])
        req = self.req
        
        req.addr ** (self.base + fitTo(self.index.data, req.addr) * ITEM_SIZE_IN_WORDS)
        req.id ** self.ID
        req.len ** (self.ITEM_SIZE_IN_WORDS - 1)
        req.rem ** 0
        

        streamSync(masters=[self.r], slaves=[self.item])
        if ITEM_SIZE_IN_WORDS == 1:
            self.item.data ** self.r.data
        else:
            raise NotImplemented("[TODO] array[%d] of registers for each data word and logic which will wait for reader of item" % ITEM_SIZE_IN_WORDS)
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = ArrayItemGetter()
    print(toRtl(u))