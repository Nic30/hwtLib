#!/usr/bin/env python3
# -*- coding: utf-8 -

from hwt.code import If, Concat, FsmBuilder
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsCastUtils import fitTo
from hwt.hdl.types.enum import HEnum
from hwt.hwIOs.std import HwIODataRdVld, HwIOVectSignal, HwIORegCntrl
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwtLib.amba.datapump.intf import AddrSizeHs, HwIOAxiWDatapump
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode
from pyMathBitPrecise.bit_utils import mask


stT = HEnum("st_t", ["waitOnInput", "waitOnDataTx", "waitOnAck"])

# [TODO] better fit of items on bus
# [TODO] fully pipeline
# [TODO] use AxiVirtualDma

@serializeParamsUniq
class ArrayBuff_writer(HwModule):
    """
    Write data in to a circula buffer allocated as an array.
    Collect items and send them over wDatapump
    when buffer is full or on timeout
    Maximum overlap of transactions is 1

    items -> buff -> internal logic -> axi datapump

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        AddrSizeHs.hwConfig(self)
        self.ID = HwParam(3)
        self.MAX_LEN = 15
        self.ITEM_WIDTH = HwParam(16)
        self.BUFF_DEPTH = HwParam(16)
        self.TIMEOUT = HwParam(1024)
        self.ITEMS = HwParam(4096 // 8)

    @override
    def hwDeclr(self):
        addClkRstn(self)

        self.items = HwIODataRdVld()
        self.items.DATA_WIDTH = self.ITEM_WIDTH

        with self._hwParamsShared():
            self.wDatapump = HwIOAxiWDatapump()._m()

        self.uploaded = HwIOVectSignal(16)._m()

        self.baseAddr = HwIORegCntrl()
        self.baseAddr.DATA_WIDTH = self.ADDR_WIDTH

        self.buff_remain = HwIOVectSignal(16)._m()

        b = HandshakedFifo(HwIODataRdVld)
        b.DATA_WIDTH = self.ITEM_WIDTH
        b.EXPORT_SIZE = True
        b.DEPTH = self.BUFF_DEPTH
        self.buff = b

    def uploadedCntrHandler(self, st, reqAckHasCome, sizeOfitems):
        uploadedCntr = self._reg(
            "uploadedCntr", self.uploaded._dtype, def_val=0)
        self.uploaded(uploadedCntr)

        If(st._eq(stT.waitOnAck) & reqAckHasCome,
           uploadedCntr(uploadedCntr + fitTo(sizeOfitems, uploadedCntr))
        )

    @override
    def hwImpl(self):
        ALIGN_BITS = log2ceil(self.DATA_WIDTH // 8 - 1)
        TIMEOUT_MAX = self.TIMEOUT - 1
        ITEMS = self.ITEMS
        buff = self.buff
        reqAck = self.wDatapump.ack
        req = self.wDatapump.req
        w = self.wDatapump.w

        propagateClkRstn(self)

        sizeOfitems = self._reg("sizeOfItems", HBits(
            buff.size._dtype.bit_length()))

        # aligned base addr
        baseAddr = self._reg("baseAddrReg", HBits(self.ADDR_WIDTH - ALIGN_BITS))
        If(self.baseAddr.dout.vld,
           baseAddr(self.baseAddr.dout.data[:ALIGN_BITS])
        )
        self.baseAddr.din(Concat(baseAddr, HBits(ALIGN_BITS).from_py(0)))

        # offset in buffer and its complement
        offset_t = HBits(log2ceil(ITEMS + 1), signed=False)
        offset = self._reg("offset", offset_t, def_val=0)
        remaining = self._reg("remaining", HBits(
            log2ceil(ITEMS + 1), signed=False), def_val=ITEMS)
        self.buff_remain(remaining, fit=True)

        addrTmp = self._sig("baseAddrTmp", baseAddr._dtype)
        addrTmp(baseAddr + fitTo(offset, baseAddr))

        # req values logic
        req.id(self.ID)
        req.addr(Concat(addrTmp, HBits(ALIGN_BITS).from_py(0)))
        req.rem(0)

        sizeTmp = self._sig("sizeTmp", buff.size._dtype)

        assert (req.len._dtype.bit_length()
                == buff.size._dtype.bit_length() - 1), (
            req.len._dtype.bit_length(), buff.size._dtype.bit_length())

        buffSizeAsLen = self._sig("buffSizeAsLen", buff.size._dtype)
        buffSizeAsLen(buff.size - 1)
        buffSize_tmp = self._sig("buffSize_tmp", remaining._dtype)
        buffSize_tmp(buff.size, fit=True)

        endOfLenBlock = (remaining - 1) < buffSize_tmp

        remainingAsLen = self._sig("remainingAsLen", remaining._dtype)
        remainingAsLen(remaining - 1)

        If(endOfLenBlock,
            req.len(remainingAsLen, fit=True),
            sizeTmp(remaining, fit=True)
        ).Else(
            req.len(buffSizeAsLen, fit=True),
            sizeTmp(buff.size)
        )

        lastWordCntr = self._reg("lastWordCntr", buff.size._dtype, 0)
        w_last = lastWordCntr._eq(1)
        w_ack = w.ready & buff.dataOut.vld

        # timeout logic
        timeoutCntr = self._reg("timeoutCntr", HBits(log2ceil(self.TIMEOUT), False),
                                def_val=TIMEOUT_MAX)
        # buffer is full or timeout
        beginReq = buff.size._eq(self.BUFF_DEPTH) | timeoutCntr._eq(0)
        reqAckHasCome = self._sig("reqAckHasCome")
        reqAckHasCome(reqAck.vld & reqAck.data._eq(self.ID))
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
            req.vld(1),
            If(req.rd,
                If(endOfLenBlock,
                   offset(0),
                   remaining(ITEMS)
                ).Else(
                    offset(offset + fitTo(buff.size, offset)),
                    remaining(remaining - fitTo(buff.size, remaining))
                ),
                sizeOfitems(sizeTmp),
                timeoutCntr(TIMEOUT_MAX)
            )
        ).Else(
            req.vld(0),
            If(buff.dataOut.vld & st._eq(stT.waitOnInput) & (timeoutCntr != 0),
               timeoutCntr(timeoutCntr - 1)
            )
        )

        reqAck.rd(st._eq(stT.waitOnAck))

        self.uploadedCntrHandler(st, reqAckHasCome, sizeOfitems)

        # it does not matter when lastWordCntr is changing when there is no
        # request
        startSendingData = st._eq(stT.waitOnInput) & beginReq & req.rd
        If(startSendingData,
            lastWordCntr(sizeTmp)
        ).Elif((lastWordCntr != 0) & w_ack,
            lastWordCntr(lastWordCntr - 1)
        )

        buff.dataIn(self.items)

        w.data(buff.dataOut.data, fit=True)

        StreamNode(
            masters=[buff.dataOut],
            slaves=[w]
        ).sync(st._eq(stT.waitOnDataTx))
        w.strb(mask(w.strb._dtype.bit_length()))
        w.last(w_last)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = ArrayBuff_writer()
    m.TIMEOUT = 32
    print(to_rtl_str(m))
