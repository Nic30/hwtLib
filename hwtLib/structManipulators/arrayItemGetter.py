from hwt.code import log2ceil, Concat, Switch
from hwt.interfaces.std import Handshaked, VectSignal
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwt.synthesizer.vectorUtils import fitTo
from hwtLib.axi.axiDatapumpIntf import AxiRDatapumpIntf
from hwtLib.handshaked.streamNode import streamSync
from hwt.hdlObjects.typeShortcuts import vec
from hwt.interfaces.utils import addClkRstn


class ArrayItemGetter(Unit):
    """
    Get specific item from array by index
    """
    def _config(self):
        self.ITEMS = Param(32)
        self.ITEM_WIDTH = Param(32)
        self.ID = Param(0)
        self.ID_WIDTH = Param(4)
        self.DATA_WIDTH = Param(64)
        self.ADDR_WIDTH = Param(32)
         
    def _declr(self):
        addClkRstn(self)
        # addr of start of array
        self.base = VectSignal(self.ADDR_WIDTH)
        
        # input index of item to get
        self.index = Handshaked()
        self.index.DATA_WIDTH.set(log2ceil(self.ITEMS))
        
        
        # output item from array
        self.item = Handshaked()
        self.item.DATA_WIDTH.set(self.ITEM_WIDTH)
        
        with self._paramsShared():
            # interface for communication with datapump
            self.rDatapump = AxiRDatapumpIntf()
            self.rDatapump.MAX_LEN.set(self.ITEMS - 1)
    
    def _impl(self):
        ITEM_WIDTH = evalParam(self.ITEM_WIDTH).val
        DATA_WIDTH = evalParam(self.DATA_WIDTH).val
        
        ITEMS_IN_DATA_WORD = DATA_WIDTH//ITEM_WIDTH
        ITEM_SIZE_IN_WORDS = 1

        if ITEM_WIDTH % 8 != 0 or ITEM_SIZE_IN_WORDS * DATA_WIDTH != ITEMS_IN_DATA_WORD * ITEM_WIDTH:
            raise NotImplementedError(ITEM_WIDTH)
        
        addr = Concat(self.index.data, vec(0, log2ceil(ITEM_WIDTH // 8)))
        
        req = self.rDatapump.req
        streamSync(masters=[self.index], slaves=[req])
        
        req.addr ** (self.base + fitTo(addr, req.addr))
        req.id ** self.ID
        req.len ** (ITEM_SIZE_IN_WORDS - 1)
        req.rem ** 0
        

        streamSync(masters=[self.rDatapump.r], slaves=[self.item])
        if ITEMS_IN_DATA_WORD == 1:
            self.item.data ** self.rDatapump.r.data
        else:
            # [TODO] itemIndex into fifo
            r = self.rDatapump.r.data
            Switch(itemIndex).addCases((i, self.item.data ** r[(ITEM_WIDTH*(i+1)): (ITEM_WIDTH *i)] 
                                        for i in range(ITEMS_IN_DATA_WORD)))
            
            
            
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = ArrayItemGetter()
    print(toRtl(u))
