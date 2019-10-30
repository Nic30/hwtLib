#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import connect, If
from hwt.interfaces.std import Signal, Handshaked, VectSignal, \
    HandshakeSync
from hwt.interfaces.utils import propagateClkRstn
from hwt.synthesizer.param import Param
from hwtLib.amba.axi4 import Axi4_w, Axi4_b, Axi4_addr
from hwtLib.amba.axi_comp.axi_datapump_intf import AxiWDatapumpIntf
from hwtLib.amba.axi_comp.axi_datapump_base import AxiDatapumpBase
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode
from pyMathBitPrecise.bit_utils import mask


class WFifoIntf(Handshaked):
    def _config(self):
        self.ID_WIDTH = Param(4)

    def _declr(self):
        self.id = VectSignal(self.ID_WIDTH)
        HandshakeSync._declr(self)


class BFifoIntf(Handshaked):
    def _config(self):
        pass

    def _declr(self):
        self.isLast = Signal()
        HandshakeSync._declr(self)


class Axi_wDatapump(AxiDatapumpBase):
    """
    Axi3/4 to axi write datapump,
    * splits request to correct request size
    * simplifies axi communication without lose of performance

    :see: :class:`hwtLib.amba.axi_comp.axi_datapump_base.AxiDatapumpBase`

    .. hwt-schematic::
    """

    def __init__(self, axiAddrCls=Axi4_addr, axiWCls=Axi4_w):
        self._axiWCls = axiWCls
        AxiDatapumpBase.__init__(self, axiAddrCls=axiAddrCls)

    def _declr(self):
        super()._declr()  # add clk, rst, axi addr channel and req channel
        with self._paramsShared():
            self.w = self._axiWCls()._m()
            self.b = Axi4_b()

            self.errorWrite = Signal()._m()
            self.driver = AxiWDatapumpIntf()

        with self._paramsShared():
            # fifo for id propagation and frame splitting on axi.w channel
            wf = self.writeInfoFifo = HandshakedFifo(WFifoIntf)
            wf.ID_WIDTH = self.ID_WIDTH
            wf.DEPTH = self.MAX_TRANS_OVERLAP

            # fifo for propagation of end of frame from axi.b channel
            bf = self.bInfoFifo = HandshakedFifo(BFifoIntf)
            bf.DEPTH = self.MAX_TRANS_OVERLAP

    def axiAwHandler(self, wErrFlag):
        req = self.driver.req
        aw = self.a
        r = self._reg

        self.axiAddrDefaults()

        wInfo = self.writeInfoFifo.dataIn
        if self.useTransSplitting():
            LEN_MAX = mask(aw.len._dtype.bit_length())

            lastReqDispatched = r("lastReqDispatched", def_val=1)
            lenDebth = r("lenDebth", req.len._dtype)
            addrBackup = r("addrBackup", req.addr._dtype)
            req_idBackup = r("req_idBackup", req.id._dtype)
            _id = self._sig("id", aw.id._dtype)

            requiresSplit = req.len > LEN_MAX
            requiresDebtSplit = lenDebth > LEN_MAX
            If(lastReqDispatched,
                _id(req.id),
                aw.addr(req.addr),
                If(requiresSplit,
                   aw.len(LEN_MAX)
                ).Else(
                    connect(req.len, aw.len, fit=True),
                ),
                req_idBackup(req.id),
                addrBackup(req.addr + self.getBurstAddrOffset()),
                lenDebth(req.len - (LEN_MAX + 1)),
                If(wInfo.rd & aw.ready & req.vld,
                    If(requiresSplit,
                       lastReqDispatched(0)
                    ).Else(
                       lastReqDispatched(1)
                    )
                ),
                StreamNode(masters=[req],
                           slaves=[aw, wInfo],
                           extraConds={aw: ~wErrFlag}).sync(),
            ).Else(
                _id(req_idBackup),
                aw.addr(addrBackup),
                If(requiresDebtSplit,
                   aw.len(LEN_MAX)
                ).Else(
                    connect(lenDebth, aw.len, fit=True)
                ),
                StreamNode(slaves=[aw, wInfo], extraConds={aw:~wErrFlag}).sync(),

                req.rd(0),

                If(StreamNode(slaves=[wInfo, aw]).ack(),
                   addrBackup(addrBackup + self.getBurstAddrOffset()),
                   lenDebth(lenDebth - (LEN_MAX+1)),
                   If(lenDebth <= LEN_MAX,
                      lastReqDispatched(1)
                   )
                )
            )
            aw.id(_id)
            wInfo.id(_id)

        else:
            aw.id(req.id)
            wInfo.id(req.id)
            aw.addr(req.addr)
            connect(req.len, aw.len, fit=True)
            StreamNode(masters=[req], slaves=[aw, wInfo]).sync()

    def axiWHandler(self, wErrFlag):
        w = self.w
        wIn = self.driver.w

        wInfo = self.writeInfoFifo.dataOut
        bInfo = self.bInfoFifo.dataIn

        if hasattr(w, "id"):
            # AXI3 has, AXI4 does not
            w.id(wInfo.id)
        w.data(wIn.data)
        w.strb(wIn.strb)

        if self.useTransSplitting():
            wordCntr = self._reg("wWordCntr", self.a.len._dtype, 0)
            doSplit = wordCntr._eq(self.getAxiLenMax()) | wIn.last

            If(StreamNode([wInfo, wIn], [bInfo, w]).ack(),
               If(doSplit,
                   wordCntr(0)
               ).Else(
                   wordCntr(wordCntr + 1)
               )
            )

        else:
            doSplit = wIn.last

        extraConds = {wInfo: doSplit,
                      bInfo: doSplit,
                      w: ~wErrFlag}
        w.last(doSplit)

        bInfo.isLast(wIn.last)
        StreamNode(masters=[wIn, wInfo],
                   slaves=[bInfo, w],
                   extraConds=extraConds
                   ).sync()

    def axiBHandler(self):
        wErrFlag = self._reg("wErrFlag", def_val=0)
        b = self.b
        ack = self.driver.ack
        lastFlags = self.bInfoFifo.dataOut

        If(lastFlags.vld & ack.rd & b.valid & (b.resp != RESP_OKAY),
           wErrFlag(1)
        )

        self.errorWrite(wErrFlag)
        ack.data(b.id)
        StreamNode(masters=[b, lastFlags],
                   slaves=[ack],
                   extraConds={
                               ack: lastFlags.isLast
                               }).sync()

        return wErrFlag

    def _impl(self):
        propagateClkRstn(self)

        wErrFlag = self.axiBHandler()
        self.axiAwHandler(wErrFlag)
        self.axiWHandler(wErrFlag)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = Axi_wDatapump()
    print(toRtl(u))
