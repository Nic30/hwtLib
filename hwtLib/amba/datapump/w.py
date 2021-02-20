#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Switch, Concat
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Signal, Handshaked, VectSignal, \
    HandshakeSync
from hwt.interfaces.utils import propagateClkRstn
from hwt.math import log2ceil
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import NotSpecified
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.amba.datapump.base import AxiDatapumpBase
from hwtLib.amba.datapump.intf import AxiWDatapumpIntf
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode
from hwtSimApi.hdlSimulator import HdlSimulator


class WFifoIntf(Handshaked):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.SHIFT_OPTIONS = Param((0,))

    def _declr(self):
        if self.SHIFT_OPTIONS != (0,):
            # The encoded value of how many bytes should be the data from input write data be shifted
            # in order to fit the word on output write bus
            self.shift = VectSignal(log2ceil(len(self.SHIFT_OPTIONS)))
            # last word can be canceled because the address can have some offset which could
            # potentially spot new word but due to limited transaction size (using req.rem)
            # this should not happen, this flags provides this information
            self.drop_last_word = Signal()

        HandshakeSync._declr(self)

    def _initSimAgent(self, sim:HdlSimulator):
        raise NotSpecified()


class BFifoIntf(Handshaked):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        pass

    def _declr(self):
        self.isLast = Signal()
        HandshakeSync._declr(self)

    def _initSimAgent(self, sim:HdlSimulator):
        raise NotSpecified()


@serializeParamsUniq
class Axi_wDatapump(AxiDatapumpBase):
    """
    Axi3/Axi3Lte/Axi4/Axi4Lite to axi write datapump,

    :see: :class:`hwtLib.amba.datapump.base.AxiDatapumpBase`

    .. hwt-autodoc::
    """

    def _declr(self):
        super()._declr()  # add clk, rst, axi addr channel and req channel

        self.errorWrite = Signal()._m()
        if self.ALIGNAS != 8:
            self.errorAlignment = Signal()._m()

        with self._paramsShared():
            self.axi.HAS_R = False
            d = self.driver = AxiWDatapumpIntf()
            d.ID_WIDTH = 0
            d.ID_WIDTH = 0
            d.MAX_BYTES = self.MAX_CHUNKS * (self.CHUNK_WIDTH // 8)

            # fifo for id propagation and frame splitting on axi.w channel
            wf = self.writeInfoFifo = HandshakedFifo(WFifoIntf)
            wf.DEPTH = self.MAX_TRANS_OVERLAP
            wf.SHIFT_OPTIONS = self.getShiftOptions()

            # fifo for propagation of end of frame from axi.b channel
            bf = self.bInfoFifo = HandshakedFifo(BFifoIntf)
            bf.DEPTH = self.MAX_TRANS_OVERLAP

    def storeTransInfo(self, transInfo: WFifoIntf, isLast: bool):
        if self.isAlwaysAligned():
            return []
        else:
            req = self.driver.req
            offset = req.addr[self.getSizeAlignBits():]
            crossesWordBoundary = self.isCrossingWordBoundary(req.addr, req.rem)
            return [
                self.encodeShiftValue(transInfo.SHIFT_OPTIONS, offset, transInfo.shift),
                transInfo.drop_last_word(~self.addrIsAligned(req.addr) & ~crossesWordBoundary)
            ]

    def axiWHandler(self, wErrFlag: RtlSignal):
        w = self.axi.w
        wIn = self.driver.w
        wInfo = self.writeInfoFifo.dataOut
        bInfo = self.bInfoFifo.dataIn

        dataAck = self._sig("dataAck")
        inLast = wIn.last
        if hasattr(w, "id"):
            # AXI3 has id signal, AXI4 does not
            w.id(self.ID_VAL)

        if self.isAlwaysAligned():
            w.data(wIn.data)
            w.strb(wIn.strb)
            if self.axi.LEN_WIDTH:
                doSplit = wIn.last
            else:
                doSplit = BIT.from_py(1)

            waitForShift = BIT.from_py(0)
        else:
            isFirst = self._reg("isFirstData", def_val=1)
            prevData = self._reg("prevData", HStruct(
                    (wIn.data._dtype, "data"),
                    (wIn.strb._dtype, "strb"),
                    (BIT, "waitingForShift"),
                ),
                def_val={"waitingForShift": 0})

            waitForShift = prevData.waitingForShift
            isShifted = (wInfo.shift != 0) | (wInfo.SHIFT_OPTIONS[0] != 0)
            wInWillWaitForShift = wIn.valid & wIn.last & isShifted & ~prevData.waitingForShift & ~wInfo.drop_last_word

            If(StreamNode([wIn, wInfo], [w, bInfo], skipWhen={wIn: waitForShift}).ack() & ~wErrFlag,
                # data feed in to prevData is stalled if we need to dispath
                # the remainder from previous word which was not yet dispatched due data shift
                # the last data from wIn is consumed on wIn.last, however there is 1 beat stall
                # for wIn i transaction was not aligned. wInfo and bInfo channels are activated
                # after last beat of wOut is send
                If(~prevData.waitingForShift,
                   prevData.data(wIn.data),
                   prevData.strb(wIn.strb),
                ),
                waitForShift(wInWillWaitForShift),
                isFirst((isShifted & waitForShift) | ((~isShifted | wInfo.drop_last_word) & wIn.last))
            )

            def applyShift(sh):
                if sh == 0 and wInfo.SHIFT_OPTIONS[0] == 0:
                    return [
                        w.data(wIn.data),
                        w.strb(wIn.strb),
                    ]
                else:
                    rem_w = self.DATA_WIDTH - sh
                    return [
                        # wIn.data starts on 0 we need to shift it sh bits
                        # in first word the prefix is invalid, in rest of the frames it is taken from
                        # previous data
                        If(waitForShift,
                            w.data(Concat(Bits(rem_w).from_py(None), prevData.data[:rem_w])),
                        ).Else(
                            w.data(Concat(wIn.data[rem_w:], prevData.data[:rem_w])),
                        ),
                        If(waitForShift,
                            # wait until remainder of previous data is send
                            w.strb(Concat(Bits(rem_w // 8).from_py(0), prevData.strb[:rem_w // 8])),
                        ).Elif(isFirst,
                            # ignore previous data
                            w.strb(Concat(wIn.strb[rem_w // 8:], Bits(sh // 8).from_py(0))),
                        ).Else(
                            # take what is left from prev data and append from wIn
                            w.strb(Concat(wIn.strb[rem_w // 8:], prevData.strb[:rem_w // 8])),
                        )
                    ]

            Switch(wInfo.shift).add_cases([
                (i, applyShift(sh))
                for i, sh in enumerate(wInfo.SHIFT_OPTIONS)
            ]).Default(
                w.data(None),
                w.strb(None),
            )
            inLast = rename_signal(self, isShifted._ternary(waitForShift | (wIn.last & wInfo.drop_last_word), wIn.last), "inLast")
            doSplit = inLast

        if self.useTransSplitting():
            wordCntr = self._reg("wWordCntr", self.getLen_t(), 0)
            doSplit = rename_signal(self, wordCntr._eq(self.getAxiLenMax()) | doSplit, "doSplit1")

            If(StreamNode([wInfo, wIn], [bInfo, w]).ack() & ~wErrFlag,
               If(doSplit,
                   wordCntr(0)
               ).Else(
                   wordCntr(wordCntr + 1)
               )
            )
        if self.AXI_CLS.LEN_WIDTH != 0:
            w.last(doSplit)

        # if this frame was split into a multiple frames wIn.last will equal 0
        bInfo.isLast(inLast)
        dataNode = StreamNode(
            masters=[wIn, wInfo],
            slaves=[bInfo, w],
            skipWhen={
                wIn: waitForShift,
            },
            extraConds={
                wIn:~waitForShift,
                wInfo: doSplit,
                bInfo: doSplit,
                w:~wErrFlag}
        )
        dataAck(dataNode.ack())
        dataNode.sync()

    def axiBHandler(self):
        b = self.axi.b
        ack = self.driver.ack
        lastFlags = self.bInfoFifo.dataOut
        StreamNode(
            masters=[b, lastFlags],
            slaves=[ack],
            extraConds={
                ack: lastFlags.isLast
            }
        ).sync()

    def _impl(self):
        propagateClkRstn(self)
        b = self.axi.b
        wErrFlag = self._reg("wErrFlag", def_val=0)
        If(b.valid & (b.resp != RESP_OKAY),
           wErrFlag(1)
        )
        self.errorWrite(wErrFlag)
        if self.ALIGNAS != 8:
            wErrAlignFlag = self._reg("wErrAlignFlag", def_val=0)
            req = self.driver.req
            If(req.vld & ~self.addrIsAligned(req.addr),
               wErrAlignFlag(1)
            )
            self.errorAlignment(wErrAlignFlag)
            wErrFlag = wErrFlag | wErrAlignFlag

        self.addrHandler(self.driver.req, self.axi.aw, self.writeInfoFifo.dataIn, wErrFlag)
        self.axiWHandler(wErrFlag)
        self.axiBHandler()


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Axi_wDatapump()
    # u.ALIGNAS = 8
    print(to_rtl_str(u))
