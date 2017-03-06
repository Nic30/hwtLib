#!/usr/bin/env python3
# -*- coding: utf-8 -

from hwt.bitmask import mask
from hwt.code import If, Concat, connect, FsmBuilder, log2ceil
from hwt.hdlObjects.typeShortcuts import vecT, vec
from hwt.hdlObjects.types.enum import Enum
from hwt.interfaces.std import Handshaked, VectSignal, RegCntrl, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.serializer.constants import SERI_MODE
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axiDatapumpIntf import AddrSizeHs, AxiWDatapumpIntf
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync


def errListeners_inputSize(self):
    inputSizeErr = self._reg("inputSizeErr_reg", defVal=0)
    self.inputSizeErr ** inputSizeErr
    If(self.items.vld & self.items.data._eq(0),
       inputSizeErr ** 1
    )

stT = Enum("st_t", ["waitOnInput", "waitOnDataTx", "waitOnAck"])


class ArrayBuff_writer(Unit):
    """
    Collect items and send them over wDatapump when buffer is full or on timeout
    Cyclically writes items into array over wDatapump
    Maximum overlap of transactions is 1

    [TODO] better fit of items on bus
    [TODO] fully pipeline

    items -> buff -> internal logic -> axi datapump
    """
    _serializerMode = SERI_MODE.PARAMS_UNIQ

    def _config(self):
        AddrSizeHs._config(self)
        self.ID = Param(3)
        self.MAX_LEN.set(16)
        self.SIZE_WIDTH = Param(16)
        self.BUFF_DEPTH = Param(16)
        self.TIMEOUT = Param(1024)
        self.ITEMS = Param(4096 // 8)

    def _declr(self):
        addClkRstn(self)

        self.items = Handshaked()
        self.items.DATA_WIDTH.set(self.SIZE_WIDTH)

        with self._paramsShared():
            self.wDatapump = AxiWDatapumpIntf()

        self.uploaded = VectSignal(16)

        self.baseAddr = RegCntrl()
        self.baseAddr.DATA_WIDTH.set(self.ADDR_WIDTH)

        self.lenBuff_remain = VectSignal(16)
        self.inputSizeErr = Signal()

        b = HandshakedFifo(Handshaked)
        b.DATA_WIDTH.set(self.SIZE_WIDTH)
        b.EXPORT_SIZE.set(True)
        b.DEPTH.set(self.BUFF_DEPTH)
        self.buff = b

    def getRegisterFile(self):
        rf = [
            self.baseAddr,
            self.uploaded,
            self.lenBuff_remain]
        return rf

    def uploadedCntrHandler(self, st, reqAckHasCome, sizeOfitems):
        uploadedCntr = self._reg("uploadedCntr", self.uploaded._dtype, defVal=0)
        self.uploaded ** uploadedCntr

        If(st._eq(stT.waitOnAck) & reqAckHasCome,
           uploadedCntr ** (uploadedCntr + sizeOfitems)
        )

    def _impl(self):
        ALIGN_BITS = log2ceil(self.DATA_WIDTH // 8 - 1).val
        TIMEOUT_MAX = self.TIMEOUT - 1
        ITEMS = self.ITEMS
        buff = self.buff
        reqAck = self.wDatapump.ack
        req = self.wDatapump.req
        w = self.wDatapump.w

        propagateClkRstn(self)

        errListeners_inputSize(self)

        sizeOfitems = self._reg("sizeOfitems", vecT(buff.size._dtype.bit_length()))

        # aligned base addr
        baseAddr = self._reg("baseAddrReg", vecT(self.ADDR_WIDTH - ALIGN_BITS))
        If(self.baseAddr.dout.vld,
           baseAddr ** self.baseAddr.dout.data[:ALIGN_BITS]
        )
        self.baseAddr.din ** Concat(baseAddr, vec(0, ALIGN_BITS))

        # offset in buffer and its complement        
        offset = self._reg("offset", vecT(log2ceil(ITEMS + 1), False), defVal=0)
        remaining = self._reg("remaining", vecT(log2ceil(ITEMS + 1), False), defVal=ITEMS)
        connect(remaining, self.lenBuff_remain, fit=True) 

        addrTmp = self._sig("baseAddrTmp", baseAddr._dtype)
        addrTmp ** (baseAddr + offset)

        # req values logic
        req.id ** self.ID
        req.addr ** Concat(addrTmp, vec(0, ALIGN_BITS))
        req.rem ** 0

        sizeTmp = self._sig("sizeTmp", buff.size._dtype)

        assert req.len._dtype.bit_length() == buff.size._dtype.bit_length() - 1, (
            req.len._dtype.bit_length(), buff.size._dtype.bit_length())

        buffSizeAsLen = self._sig("buffSizeAsLen", buff.size._dtype)
        buffSizeAsLen ** (buff.size - 1)
        buffSize_tmp = self._sig("buffSize_tmp", remaining._dtype)
        connect(buff.size, buffSize_tmp, fit=True)

        endOfLenBlock = (remaining - 1) < buffSize_tmp

        remainingAsLen = self._sig("remainingAsLen", remaining._dtype)
        remainingAsLen ** (remaining - 1)

        If(endOfLenBlock,
            connect(remainingAsLen, req.len, fit=True),
            connect(remaining, sizeTmp, fit=True)
        ).Else(
            connect(buffSizeAsLen, req.len, fit=True),
            sizeTmp ** buff.size
        )

        lastWordCntr = self._reg("lastWordCntr", buff.size._dtype, 0)
        w_last = lastWordCntr._eq(1)
        w_ack = w.ready & buff.dataOut.vld

        # timeout logic
        timeoutCntr = self._reg("timeoutCntr", vecT(log2ceil(self.TIMEOUT), False),
                                defVal=TIMEOUT_MAX)
        beginReq = buff.size._eq(self.BUFF_DEPTH) | timeoutCntr._eq(0)  # buffer is full or timeout
        reqAckHasCome = self._sig("reqAckHasCome")
        reqAckHasCome ** (reqAck.vld & reqAck.data._eq(self.ID))
        st = FsmBuilder(self, stT)\
        .Trans(stT.waitOnInput,
            (beginReq & req.rd, stT.waitOnDataTx)

        ).Trans(stT.waitOnDataTx,
            (w_last & w_ack, stT.waitOnAck)

        ).Trans(stT.waitOnAck,
            (reqAckHasCome, stT.waitOnInput)

        ).stateReg

        If(st._eq(stT.waitOnInput) & beginReq,  # timeout is counting only when there is pending data
            # start new request
            req.vld ** 1,
            If(req.rd,
                If(endOfLenBlock,
                   offset ** 0,
                   remaining ** ITEMS
                ).Else(
                   offset ** (offset + buff.size),
                   remaining ** (remaining - buff.size)
                ),
                sizeOfitems ** sizeTmp,
                timeoutCntr ** TIMEOUT_MAX
            )
        ).Else(
            req.vld ** 0,
            If(buff.dataOut.vld & st._eq(stT.waitOnInput) & (timeoutCntr != 0),
               timeoutCntr ** (timeoutCntr - 1)
            )
        )

        reqAck.rd ** st._eq(stT.waitOnAck)

        self.uploadedCntrHandler(st, reqAckHasCome, sizeOfitems)

        # it does not matter when lastWordCntr is changing when there is no request
        startSendingData = st._eq(stT.waitOnInput) & beginReq & req.rd
        If(startSendingData,
            lastWordCntr ** sizeTmp
        ).Elif((lastWordCntr != 0) & w_ack,
            lastWordCntr ** (lastWordCntr - 1)
        )

        buff.dataIn ** self.items

        connect(buff.dataOut.data, w.data, fit=True)

        streamSync(masters=[buff.dataOut],
                   slaves=[w],
                   extraConds={buff.dataOut: [st._eq(stT.waitOnDataTx)],
                               w:            [st._eq(stT.waitOnDataTx)]
                               })
        w.strb ** mask(w.strb._dtype.bit_length())
        w.last ** w_last

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = ArrayBuff_writer()
    u.TIMEOUT.set(32)
    print(toRtl(u))
