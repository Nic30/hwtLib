from hdl_toolkit.hdlObjects.typeShortcuts import vecT, vec
from hdl_toolkit.interfaces.std import Handshaked, RegCntrl, VectSignal
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn, log2ceil
from hdl_toolkit.synthesizer.codeOps import If, In, Concat, connect
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param
from hwtLib.axi.axi_datapump_base import AddrSizeHs
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync
from hwtLib.interfaces.amba import AxiStream_withId
from hdl_toolkit.synthesizer.vectorUtils import fitTo


class CLinkedListReader(Unit):
    """
    This unit reads items from circular linked list like structure 
    
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
        self.DEFAULT_ID = Param(3)
        # id of packet where last item is next addr
        self.LAST_ID = Param(4)

        self.BUFFER_CAPACITY = Param(32)
        self.ITEMS_IN_BLOCK = Param(4096 // 8 - 1)

        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.RING_SPACE_WIDTH = Param(16)

    def _declr(self):
        addClkRstn(self)
        
        with self._paramsShared():
            # interface which sending requests to download data
            self.req = AddrSizeHs()
            self.req.MAX_LEN.set(self.BUFFER_CAPACITY // 2 - 1)
            
            # interface which is collecting all data and only data with specified id are processed
            self.r = AxiStream_withId()
            self.dataOut = Handshaked()
            
        # (how much of items remains in block)
        self.inBlockRemain = VectSignal(log2ceil(self.ITEMS_IN_BLOCK + 1))
        
        # interface to control internal register
        self.baseAddr = RegCntrl()
        self.baseAddr.DATA_WIDTH.set(self.ADDR_WIDTH)
        self.rdPtr = RegCntrl()
        self.wrPtr = RegCntrl()
        for ptr in [self.rdPtr, self.wrPtr]:
            ptr.DATA_WIDTH.set(self.RING_SPACE_WIDTH)
                

        f = self.dataFifo = HandshakedFifo(Handshaked)
        f.EXPORT_SIZE.set(True)
        f.DATA_WIDTH.set(self.DATA_WIDTH)
        f.DEPTH.set(self.BUFFER_CAPACITY)
        
    def addrAlignBits(self):
        return log2ceil(self.DATA_WIDTH // 8).val
    
    def _impl(self):
        propagateClkRstn(self)
        r, s = self._reg, self._sig
        req = self.req
        f = self.dataFifo
        dIn = self.r
        ALIGN_BITS = self.addrAlignBits()
        DEFAULT_ID = self.DEFAULT_ID
        BUFFER_CAPACITY = self.BUFFER_CAPACITY
        BURST_LEN = BUFFER_CAPACITY // 2
        LAST_ID = self.LAST_ID
        bufferHasSpace = s("bufferHasSpace")
        bufferHasSpace ** (f.size < (BURST_LEN + 1))
        # we are counting base next addr as item as well
        inBlock_t = vecT(log2ceil(self.ITEMS_IN_BLOCK + 1))
        ringSpace_t = vecT(self.RING_SPACE_WIDTH)
        
        downloadPending = r("downloadPending", defVal=0)
        
        # [TODO] maybe can be only index of page
        baseIndex = r("baseIndex", vecT(self.ADDR_WIDTH - ALIGN_BITS))
        inBlockRemain = r("inBolockRemain_reg", inBlock_t, defVal=self.ITEMS_IN_BLOCK)
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
        isMyData = dIn.valid & In(dIn.id, [DEFAULT_ID, LAST_ID])
        
        If(self.baseAddr.dout.vld,
            baseIndex ** self.baseAddr.dout.data[:ALIGN_BITS]
        ).Elif(isMyData & downloadPending,
            If(dIn.last & dIn.id._eq(LAST_ID),
               baseIndex ** dIn.data[self.ADDR_WIDTH:ALIGN_BITS]
            ).Else(
               baseIndex ** (baseIndex + 1) 
            )
        )
        
        # logic of inBolockRemain, req.id, req.len
        nextButrstCanContainBaseAddr = r("nextButrstCanContainBaseAddr", defVal=False)
        sizeByPtrs = s("sizeByPtrs", ringSpace_t)
        sizeByPtrs ** (wrPtr - rdPtr)
        
        inBlockRemain_asPtrSize = fitTo(inBlockRemain, sizeByPtrs)
        isConstraindedByPtrs = s("isConstraindedByPtrs")
        isConstraindedByPtrs ** (sizeByPtrs < inBlockRemain_asPtrSize)
        
        canDownloadNextBaseAddrInThisReq = s("canDownloadNextBaseAddrInThisReq")
        canDownloadNextBaseAddrInThisReq ** (sizeByPtrs + inBlockRemain_asPtrSize)._eq(self.ITEMS_IN_BLOCK - 1)
        
        If(nextButrstCanContainBaseAddr,
            If(isConstraindedByPtrs & canDownloadNextBaseAddrInThisReq,
                req.id ** DEFAULT_ID,
                connect(sizeByPtrs - 1, req.len, fit=True),
                
                If(doReq,
                    connect(inBlockRemain_asPtrSize - sizeByPtrs, inBlockRemain, fit=True),
                    nextButrstCanContainBaseAddr ** True
                )
            ).Else(
                req.id ** LAST_ID,
                # means burst of size inBlockRemain + 1, last item will be next base addr 
                connect(inBlockRemain, req.len, fit=True),
                
                If(doReq,
                   inBlockRemain ** self.ITEMS_IN_BLOCK,
                   nextButrstCanContainBaseAddr ** False
                )
            )
        
        ).Else(
            req.id ** DEFAULT_ID,
            If(isConstraindedByPtrs,
                connect(sizeByPtrs - 1, req.len, fit=True)
            ).Else(
                req.len ** (BURST_LEN - 1),
            ),
            
            If(doReq,
                If(isConstraindedByPtrs,
                   connect(inBlockRemain_asPtrSize - sizeByPtrs, inBlockRemain, fit=True),
                   nextButrstCanContainBaseAddr ** ((inBlockRemain_asPtrSize - sizeByPtrs) < BURST_LEN)
                ).Else(
                   inBlockRemain ** (inBlockRemain - BURST_LEN),
                   nextButrstCanContainBaseAddr ** (inBlockRemain < (BURST_LEN * 2))
                )
            )
        )
        
        # logic of req dispatching
        If(downloadPending,
            req.vld ** 0,
            If(isMyData & dIn.last,
                downloadPending ** 0
            )
        ).Else(
            req.vld ** (bufferHasSpace & hasSpace),
            If(bufferHasSpace,
               downloadPending ** hasSpace
            )
        )
        
        # into buffer pushing logic
        dBuffIn = f.dataIn
        dBuffIn.data ** dIn.data
        
        receivingData = s("receivingData")
        receivingData ** (dIn.valid & (dIn.id._eq(DEFAULT_ID) | (~dIn.last & dIn.id._eq(LAST_ID))))
        If(self.rdPtr.dout.vld,
            rdPtr ** self.rdPtr.dout.data
        ).Else(
            If(receivingData & downloadPending & dBuffIn.rd,
               rdPtr ** (rdPtr + 1)
            )
        )
        streamSync([dIn], [dBuffIn], extraConds={dIn    :[receivingData, downloadPending],
                                                 dBuffIn:[receivingData, downloadPending]})
    
       
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = CLinkedListReader()
    print(toRtl(u))
            
        
