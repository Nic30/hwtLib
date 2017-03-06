#!/usr/bin/env python3
# -*- coding: utf-8 -

from hwt.code import If, In, Concat, connect, log2ceil
from hwt.hdlObjects.typeShortcuts import vecT, vec
from hwt.interfaces.std import Handshaked, RegCntrl, VectSignal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.vectorUtils import fitTo
from hwtLib.amba.axiDatapumpIntf import AxiRDatapumpIntf
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync


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

    def getRegisterFile(self):
        return [
                self.baseAddr,
                self.rdPtr,
                self.wrPtr,
                self.inBlockRemain
               ]

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

        baseIndex = r("baseIndex", vecT(self.ADDR_WIDTH - ALIGN_BITS))
        inBlockRemain = r("inBlockRemain_reg", inBlock_t, defVal=self.ITEMS_IN_BLOCK)
        self.inBlockRemain ** inBlockRemain

        # Logic of tail/head
        rdPtr = r("rdPtr", ringSpace_t, defVal=0)
        wrPtr = r("wrPtr", ringSpace_t, defVal=0)
        If(self.wrPtr.dout.vld,
            wrPtr ** self.wrPtr.dout.data
        )
        self.wrPtr.din ** wrPtr
        self.rdPtr.din ** rdPtr

        # this means items are present in memory
        hasSpace = s("hasSpace")
        hasSpace ** (wrPtr != rdPtr)
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

        constrainedByInBlockRemain = s("constrainedByInBlockRemain")
        constrainedByInBlockRemain ** (fitTo(sizeByPtrs, inBlockRemain) >= inBlockRemain)
        
        If(constraingSpace > BURST_LEN,
            # download full burst
            req.id ** ID,
            req.len ** (BURST_LEN - 1),
            If(doReq,
               inBlockRemain ** (inBlockRemain - BURST_LEN)
            )
        ).Elif(constrainedByInBlockRemain & (inBlockRemain < BURST_LEN),
            # we know that sizeByPtrs <= inBlockRemain thats why we can resize it
            # we will download next* as well
            req.id ** ID_LAST,
            connect(constraingSpace, req.len, fit=True),
            If(doReq,
               inBlockRemain ** self.ITEMS_IN_BLOCK
            )
        ).Else(
            # download data leftover
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
            If(req.rd & bufferHasSpace & hasSpace,
               downloadPending ** 1
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
        # push data into buffer and increment rdPtr
        streamSync(masters=[dIn],
                   slaves=[dBuffIn],
                   extraConds={dIn    :[downloadPending],
                               dBuffIn:[dIn.id._eq(ID) | (dIn.id._eq(ID_LAST) & ~dIn.last), downloadPending]
                               })

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = CLinkedListReader()
    u.BUFFER_CAPACITY.set(8)
    u.ITEMS_IN_BLOCK.set(31)
    u.PTR_WIDTH.set(8)
    print(toRtl(u))
