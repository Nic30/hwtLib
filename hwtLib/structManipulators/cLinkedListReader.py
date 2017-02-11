from hwt.hdlObjects.typeShortcuts import vecT, vec
from hwt.interfaces.std import Handshaked, RegCntrl, VectSignal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.code import If, In, Concat, connect, log2ceil
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.vectorUtils import fitTo
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync
from hwtLib.axi.axiDatapumpIntf import AxiRDatapumpIntf


class CLinkedListReader(Unit):
    """
    This unit reads items from (circular) linked list like structure 
    
    struct node {
        item_t items[ITEMS_IN_BLOCK],
        struct node * next; 
    };
    
    synchronization is obtained by rdPtr/wrPtr (tail/head) pointer
    baseAddr is address of actual node
    
    @attention: device reads only chunks of size <= BUFFER_CAPACITY/2,
    """
    def _config(self):
        self.ID_WIDTH = Param(4)
        self.ID = Param(3)
        # id of packet where last item is next addr
        self.ID_LAST = Param(4)

        self.BUFFER_CAPACITY = Param(32)
        self.ITEMS_IN_BLOCK = Param(4096 // 8 - 1)

        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.PTR_WIDTH = Param(16)

    def _declr(self):
        addClkRstn(self)
        
        with self._paramsShared():
            # interface which sending requests to download data
            # and interface which is collecting all data and only data with specified id are processed
            self.rDatapump = AxiRDatapumpIntf()
            self.rDatapump.MAX_LEN.set(self.BUFFER_CAPACITY // 2 - 1)
            
            self.dataOut = Handshaked()
            
        # (how much of items remains in block)
        self.inBlockRemain = VectSignal(log2ceil(self.ITEMS_IN_BLOCK + 1))
        
        # interface to control internal register
        self.baseAddr = RegCntrl()
        self.baseAddr._replaceParam("DATA_WIDTH", self.ADDR_WIDTH)
        self.rdPtr = RegCntrl()
        self.wrPtr = RegCntrl()
        for ptr in [self.rdPtr, self.wrPtr]:
            ptr._replaceParam("DATA_WIDTH", self.PTR_WIDTH)
                

        f = self.dataFifo = HandshakedFifo(Handshaked)
        f.EXPORT_SIZE.set(True)
        f.DATA_WIDTH.set(self.DATA_WIDTH)
        f.DEPTH.set(self.BUFFER_CAPACITY)
        
    def addrAlignBits(self):
        return log2ceil(self.DATA_WIDTH // 8).val
    
    def _impl(self):
        propagateClkRstn(self)
        r, s = self._reg, self._sig
        req = self.rDatapump.req
        f = self.dataFifo
        dIn = self.rDatapump.r
        dBuffIn = f.dataIn
                
        ALIGN_BITS = self.addrAlignBits()
        ID = self.ID
        BUFFER_CAPACITY = self.BUFFER_CAPACITY
        BURST_LEN = BUFFER_CAPACITY // 2
        ID_LAST = self.ID_LAST
        bufferHasSpace = s("bufferHasSpace")
        bufferHasSpace ** (f.size < (BURST_LEN + 1))
        # we are counting base next addr as item as well
        inBlock_t = vecT(log2ceil(self.ITEMS_IN_BLOCK + 1))
        ringSpace_t = vecT(self.PTR_WIDTH)
        
        downloadPending = r("downloadPending", defVal=0)
        
        # [TODO] maybe can be only index of page
        baseIndex = r("baseIndex", vecT(self.ADDR_WIDTH - ALIGN_BITS))
        inBlockRemain = r("inBlockRemain_reg", inBlock_t, defVal=self.ITEMS_IN_BLOCK)
        self.inBlockRemain ** inBlockRemain

        # Logic of tail/head, 
        rdPtr = r("rdPtr", ringSpace_t, defVal=0)
        wrPtr = r("wrPtr", ringSpace_t, defVal=0)
        If(self.wrPtr.dout.vld,
            wrPtr ** self.wrPtr.dout.data
        )
        self.wrPtr.din ** wrPtr
        self.rdPtr.din ** rdPtr
        
        # this means items are present in memory
        hasSpace = (wrPtr != rdPtr) 
        doReq = s("doReq")
        doReq ** (bufferHasSpace & hasSpace & ~downloadPending & req.rd)
        req.rem ** 0  
        self.dataOut ** f.dataOut 
             
        # logic of baseAddr and baseIndex
        baseAddr = Concat(baseIndex, vec(0, ALIGN_BITS))
        req.addr ** baseAddr
        self.baseAddr.din ** baseAddr
        dataAck = dIn.valid & In(dIn.id, [ID, ID_LAST]) & dBuffIn.rd
        
        If(self.baseAddr.dout.vld,
            baseIndex ** self.baseAddr.dout.data[:ALIGN_BITS]
        ).Elif(dataAck & downloadPending,
            If(dIn.last & dIn.id._eq(ID_LAST),
               baseIndex ** dIn.data[self.ADDR_WIDTH:ALIGN_BITS]
            ).Else(
               baseIndex ** (baseIndex + 1) 
            )
        )
        
        sizeByPtrs = s("sizeByPtrs", ringSpace_t)
        sizeByPtrs ** (wrPtr - rdPtr)
        
        inBlockRemain_asPtrSize = fitTo(inBlockRemain, sizeByPtrs)
        constraingSpace = s("constraingSpace", ringSpace_t)
        If(inBlockRemain_asPtrSize < sizeByPtrs,
           constraingSpace ** inBlockRemain_asPtrSize
        ).Else(
           constraingSpace ** sizeByPtrs
        )
        
        If(constraingSpace > BURST_LEN,
            # download full burst
            req.id ** ID,
            req.len ** (BURST_LEN - 1),
            If(doReq,
               inBlockRemain ** (inBlockRemain - BURST_LEN)
            )
        ).Elif((fitTo(sizeByPtrs, inBlockRemain) >= inBlockRemain) & (inBlockRemain < BURST_LEN),
            # we know that sizeByPtrs <= inBlockRemain thats why we cane resize it
            # we will download next* as well
            req.id ** ID_LAST,
            connect(constraingSpace, req.len, fit=True),
            If(doReq,
               inBlockRemain ** (inBlockRemain - (fitTo(constraingSpace, inBlockRemain) + 1))
            )
        ).Else(
            # download leftover
            req.id ** ID,
            connect(constraingSpace - 1, req.len, fit=True),
            If(doReq,
               inBlockRemain ** (inBlockRemain - fitTo(constraingSpace, inBlockRemain))
            )
        )

        # logic of req dispatching
        If(downloadPending,
            req.vld ** 0,
            If(dataAck & dIn.last,
                downloadPending ** 0
            )
        ).Else(
            req.vld ** (bufferHasSpace & hasSpace),
            If(bufferHasSpace,
               downloadPending ** hasSpace
            )
        )
        
        # into buffer pushing logic

        dBuffIn.data ** dIn.data
        
        isMyData = s("isMyData")
        isMyData ** (dIn.id._eq(ID) | (~dIn.last & dIn.id._eq(ID_LAST)))
        If(self.rdPtr.dout.vld,
            rdPtr ** self.rdPtr.dout.data
        ).Else(
            If(dIn.valid & downloadPending & dBuffIn.rd & isMyData,
               rdPtr ** (rdPtr + 1)
            )
        )
        # ignore data if not my data
        # notMyData = ~In(dIn.id, [ID, ID_LAST])
        # streamSync([dIn], [dBuffIn], extraConds={dIn   :[downloadPending | notMyData],
        #                                        dBuffIn:[receivingData, downloadPending]})
        #
        If(dIn.valid & In(dIn.id, [ID, ID_LAST]),
           # push data into buffer and increment rdPtr
           streamSync(masters=[dIn],
                      slaves=[dBuffIn],
                      extraConds={dIn    :[downloadPending],
                                  dBuffIn:[~((dIn.id._eq(ID_LAST)) & dIn.last), downloadPending]})
        ).Else(
           # ship next block addr
           dBuffIn.vld ** 0,
           dIn.ready ** 1   
        )
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = CLinkedListReader()
    u.BUFFER_CAPACITY.set(8)
    u.ITEMS_IN_BLOCK.set(31)
    u.PTR_WIDTH.set(8)
    print(toRtl(u))
            
        
