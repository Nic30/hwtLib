#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat, connect, log2ceil, FsmBuilder, power
from hwt.hdl.typeShortcuts import vec
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.std import Handshaked, RegCntrl
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.vectorUtils import fitTo
from hwtLib.amba.axi_comp.axi_datapump_intf import AxiRDatapumpIntf, AxiWDatapumpIntf
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode
from pyMathBitPrecise.bit_utils import mask


class CLinkedListWriter(Unit):
    """
    This unit writes items to (circular) linked list like structure
    (List does not necessary need to be circular but space is specified
    by two pointers like in circular queue)

    .. code-block:: c

        struct node {
            item_t items[ITEMS_IN_BLOCK],
            struct node * next;
        };

    synchronization is obtained by rdPtr/wrPtr (tail/head) pointer
    baseAddr is address of actual node

    :attention: device writes chunks of max size <= BUFFER_CAPACITY/2
    :attention: next addr is downloaded on background when items are uploaded
               (= has to be set when this unit enters this block)

    :note: wrPtr == rdPtr   => queue is empty
        and there is (2^PTR_WIDTH) - 1 of empty space
        wrPtr == rdPtr+1 => queue is full
        wrPtr+1 == rdPtr   => there is (2^PTR_WIDTH) - 2 of empty space
        spaceToWrite = rdPtr - wrPtr - 1 (with uint16_t)

    .. hwt-schematic::
    """
    def _config(self):
        self.ID_WIDTH = Param(4)
        # id on interfaces for default transaction
        self.ID = Param(3)

        self.BUFFER_CAPACITY = Param(32)
        self.ITEMS_IN_BLOCK = Param(4096 // 8 - 1)

        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.PTR_WIDTH = Param(16)

        # timeout to send items from buffer even if they are smaller
        # than recomended burst
        self.TIMEOUT = Param(4096)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            # read interface for datapump
            # interface which sending requests to download addr of next block
            self.rDatapump = AxiRDatapumpIntf()._m()
            # because we are downloading only addres of next block
            self.rDatapump.MAX_LEN = 1

            # write interface for datapump
            self.wDatapump = AxiWDatapumpIntf()._m()
            self.wDatapump.MAX_LEN = self.BUFFER_CAPACITY // 2
            assert self.BUFFER_CAPACITY <= self.ITEMS_IN_BLOCK

            # interface for items which should be written into list
            self.dataIn = Handshaked()

        # interface to control internal register
        a = self.baseAddr = RegCntrl()
        a.DATA_WIDTH = self.ADDR_WIDTH

        self.rdPtr = RegCntrl()
        self.wrPtr = RegCntrl()
        for ptr in [self.rdPtr, self.wrPtr]:
            ptr.DATA_WIDTH = self.PTR_WIDTH

        f = self.dataFifo = HandshakedFifo(Handshaked)
        f.EXPORT_SIZE = True
        f.DATA_WIDTH = self.DATA_WIDTH
        f.DEPTH = self.BUFFER_CAPACITY

        self.ALIGN_BITS = log2ceil(self.DATA_WIDTH // 8)

    def addrToIndex(self, addr):
        return addr[:self.ALIGN_BITS]

    def indexToAddr(self, indx):
        return Concat(indx, vec(0, self.ALIGN_BITS))

    def rReqHandler(self, baseIndex, doReq):
        # always download only one word with address of next block
        rReq = self.rDatapump.req
        rReq.addr(self.indexToAddr(baseIndex + self.ITEMS_IN_BLOCK))
        rReq.id(self.ID)
        rReq.len(0)
        rReq.rem(0)

        rReq.vld(doReq)

    def baseAddrLogic(self, nextBlockTransition_in):
        """
        Logic for downloading address of next block

        :param nextBlockTransition_in: signal which means that baseIndex
               should be changed to nextBaseIndex if nextBaseAddrReady
               is not high this signal has no effect (= regular handshake)
        :return: (baseIndex, nextBaseIndex, nextBaseReady is ready
                 and nextBlockTransition_in can be used)
        """
        r = self._reg
        rIn = self.rDatapump.r
        rReq = self.rDatapump.req

        addr_index_t = Bits(self.ADDR_WIDTH - self.ALIGN_BITS)
        baseIndex = r("baseIndex_backup", addr_index_t)
        nextBaseIndex = r("nextBaseIndex", addr_index_t)
        t = HEnum("nextBaseFsm_t",
                  ["uninitialized",
                   "required",
                   "pending",
                   "prepared"])
        isNextBaseAddr = rIn.valid & rIn.id._eq(self.ID)
        nextBaseFsm = FsmBuilder(self, t, "baseAddrLogic_fsm")\
        .Trans(t.uninitialized,
            (self.baseAddr.dout.vld, t.required)
        ).Trans(t.required,
            (rReq.rd, t.pending)
        ).Trans(t.pending,
            (isNextBaseAddr, t.prepared)
        ).Trans(t.prepared,
            (nextBlockTransition_in, t.required)
        ).stateReg

        If(self.baseAddr.dout.vld,
           baseIndex(self.addrToIndex(self.baseAddr.dout.data)),
        ).Elif(nextBlockTransition_in,
           baseIndex(nextBaseIndex)
        )
        self.baseAddr.din(self.indexToAddr(baseIndex))

        If(isNextBaseAddr,
           nextBaseIndex(self.addrToIndex(fitTo(rIn.data, rReq.addr)))
        )
        rIn.ready(1)

        self.rReqHandler(baseIndex, nextBaseFsm._eq(t.required))

        nextBaseReady = nextBaseFsm._eq(t.prepared)
        return baseIndex, nextBaseIndex, nextBaseReady 

    def timeoutHandler(self, rst, incr):
        timeoutCntr = self._reg("timeoutCntr",
                                Bits(log2ceil(self.TIMEOUT) + 1, signed=False),
                                def_val=self.TIMEOUT)
        If(rst,
           timeoutCntr(self.TIMEOUT)
        ).Elif((timeoutCntr != 0) & incr,
           timeoutCntr(timeoutCntr - 1)
        )
        return timeoutCntr._eq(0) 

    def queuePtrLogic(self, wrPtrIncrVal, wrPtrIncrEn):
        r, s = self._reg, self._sig
        ringSpace_t = Bits(self.PTR_WIDTH)

        # Logic of tail/head, 
        rdPtr = r("rdPtr", ringSpace_t, def_val=0)
        wrPtr = r("wrPtr", ringSpace_t, def_val=(2 ** self.PTR_WIDTH) - 1)

        If(self.wrPtr.dout.vld,
           wrPtr(self.wrPtr.dout.data)
        ).Elif(wrPtrIncrEn,
           wrPtr(wrPtr + wrPtrIncrVal)
        )

        If(self.rdPtr.dout.vld,
           rdPtr(self.rdPtr.dout.data)
        )
        self.wrPtr.din(wrPtr)
        self.rdPtr.din(rdPtr)

        lenByPtrs = s("lenByPtrs", ringSpace_t)
        lenByPtrs(rdPtr - wrPtr - 2)  # size - 1

        # this means items are present in memory
        queueHasSpace = (wrPtr + 1 != rdPtr)
        return queueHasSpace, lenByPtrs

    def wReqDriver(self, en, baseIndex, lenByPtrs, inBlockRemain):
        s = self._sig
        wReq = self.wDatapump.req
        BURST_LEN = self.BUFFER_CAPACITY // 2 - 1
        inBlockRemain_asPtrSize = fitTo(inBlockRemain, lenByPtrs)

        # wReq driver
        ringSpace_t = Bits(self.PTR_WIDTH)
        constraingLen = s("constraingSpace", ringSpace_t)

        If(inBlockRemain_asPtrSize < lenByPtrs,
          constraingLen(inBlockRemain_asPtrSize)
        ).Else(
          constraingLen(lenByPtrs)
        )
        reqLen = s("reqLen", wReq.len._dtype)
        If(constraingLen > BURST_LEN,
           reqLen(BURST_LEN)
        ).Else(
           connect(constraingLen, reqLen, fit=True)
        )

        wReq.id(self.ID)
        wReq.addr(self.indexToAddr(baseIndex))
        wReq.rem(0)
        wReq.len(reqLen)
        wReq.vld(en)

        return reqLen

    def mvDataToW(self, prepareEn, dataMoveEn, reqLen, inBlockRemain,
                  nextBlockTransition_out, dataCntr_out):
        f = self.dataFifo.dataOut
        w = self.wDatapump.w
        nextBlockTransition = self._sig("mvDataToW_nextBlockTransition")
        nextBlockTransition(inBlockRemain <= fitTo(reqLen, inBlockRemain) + 1)
        If(prepareEn,
            dataCntr_out(fitTo(reqLen, dataCntr_out)),

            If(nextBlockTransition_out,
                inBlockRemain(self.ITEMS_IN_BLOCK)
            ).Else(
                inBlockRemain(inBlockRemain - (fitTo(reqLen, inBlockRemain) + 1))
            )
        ).Elif(dataMoveEn,
            If(StreamNode(masters=[f], slaves=[w]).ack(),
               dataCntr_out(dataCntr_out - 1)
            )
        )
        StreamNode(masters=[f], slaves=[w]).sync(dataMoveEn)
        w.data(f.data)
        w.last(dataCntr_out._eq(0))
        w.strb(mask(w.strb._dtype.bit_length()))
        self.dataFifo.dataIn(self.dataIn)
        nextBlockTransition_out(nextBlockTransition & prepareEn)

    def itemUploadLogic(self, baseIndex, nextBaseIndex, nextBaseReady,
                        nextBlockTransition_out):
        r, s = self._reg, self._sig
        f = self.dataFifo
        w = self.wDatapump

        BURST_LEN = self.BUFFER_CAPACITY // 2
        bufferHasData = s("bufferHasData")
        bufferHasData(f.size > (BURST_LEN - 1))
        # we are counting base next addr as item as well
        addr_index_t = Bits(self.ADDR_WIDTH - self.ALIGN_BITS)
        baseIndex = r("baseIndex", addr_index_t)

        dataCntr_t = Bits(log2ceil(BURST_LEN + 1), signed=False)
        # counter of uploading data
        dataCntr = r("dataCntr", dataCntr_t, def_val=0)
        reqLen_backup = r("reqLen_backup", w.req.len._dtype, def_val=0)

        gotWriteAck = w.ack.vld & w.ack.data._eq(self.ID)
        queueHasSpace, lenByPtrs = self.queuePtrLogic(
            fitTo(reqLen_backup, self.wrPtr.din) + 1,
            gotWriteAck)

        timeout = s("timeout")
        fsm_t = HEnum("itemUploadingFsm_t",
                      ["idle",
                       "reqPending",
                       "dataPending_prepare",
                       "dataPending_send",
                       "waitForAck"])
        fsm = FsmBuilder(self, fsm_t, "itemUploadLogic_fsm")\
        .Trans(fsm_t.idle,
            (timeout | (bufferHasData & queueHasSpace), fsm_t.reqPending)

        ).Trans(fsm_t.reqPending,
            (w.req.rd, fsm_t.dataPending_prepare)

        ).Trans(fsm_t.dataPending_prepare,
            fsm_t.dataPending_send
        ).Trans(fsm_t.dataPending_send,
            ((~nextBlockTransition_out | nextBaseReady) & dataCntr._eq(0), fsm_t.waitForAck)
        ).Trans(fsm_t.waitForAck,
            (gotWriteAck, fsm_t.idle)    
        ).stateReg

        timeout(self.timeoutHandler(fsm != fsm_t.idle,
                                    (f.size != 0) & queueHasSpace))

        inBlock_t = Bits(log2ceil(self.ITEMS_IN_BLOCK + 1))
        inBlockRemain = r("inBlockRemain_reg", inBlock_t, def_val=self.ITEMS_IN_BLOCK)

        wReqEn = fsm._eq(fsm_t.reqPending)
        reqLen = self.wReqDriver(wReqEn, baseIndex, lenByPtrs, inBlockRemain)

        If(wReqEn & w.req.rd,
           reqLen_backup(reqLen)
        )

        dataMoveEn = fsm._eq(fsm_t.dataPending_send)
        prepareEn = fsm._eq(fsm_t.dataPending_prepare)
        self.mvDataToW(prepareEn, dataMoveEn, reqLen_backup,
                       inBlockRemain, nextBlockTransition_out, dataCntr)

        If(self.baseAddr.dout.vld,
           baseIndex(self.addrToIndex(self.baseAddr.dout.data)),
        ).Elif(prepareEn,
           baseIndex(baseIndex + fitTo(reqLen_backup, baseIndex) + 1)
        ).Elif(nextBlockTransition_out,
           baseIndex(nextBaseIndex)
        )

        w.ack.rd(fsm._eq(fsm_t.waitForAck))

    def _impl(self):
        propagateClkRstn(self)
        nextBlockTransition = self._sig("nextBlockTransition")
        baseIndex, nextBaseIndex, nextBaseReady = self.baseAddrLogic(
            nextBlockTransition)
        self.itemUploadLogic(baseIndex, nextBaseIndex, nextBaseReady,
                             nextBlockTransition)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = CLinkedListWriter()
    u.BUFFER_CAPACITY = 8
    u.ITEMS_IN_BLOCK = 31
    u.PTR_WIDTH = 8
    print(toRtl(u))
