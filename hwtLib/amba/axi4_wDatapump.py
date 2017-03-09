#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.bitmask import mask
from hwt.code import connect, If
from hwt.interfaces.std import Signal, Handshaked, VectSignal, \
    HandshakeSync
from hwt.interfaces.utils import propagateClkRstn
from hwt.synthesizer.param import Param
from hwtLib.amba.axi4 import Axi4_w, Axi4_b
from hwtLib.amba.axiDatapumpIntf import AxiWDatapumpIntf
from hwtLib.amba.axi_datapump_base import Axi_datapumpBase
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync, streamAck


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


class Axi_wDatapump(Axi_datapumpBase):
    """
    Axi3/4 to axi write datapump,
    * splits request to correct request size
    * simplifies axi communication without lose of performance 
    \n""" + Axi_datapumpBase.__doc__

    def _declr(self):
        super()._declr()  # add clk, rst, axi addr channel and req channel
        with self._paramsShared():
            self.w = Axi4_w()
            self.b = Axi4_b()

            self.errorWrite = Signal()
            self.driver = AxiWDatapumpIntf()

        with self._paramsShared():
            # fifo for id propagation and frame splitting on axi.w channel 
            wf = self.writeInfoFifo = HandshakedFifo(WFifoIntf)
            wf.ID_WIDTH.set(self.ID_WIDTH)
            wf.DEPTH.set(self.MAX_TRANS_OVERLAP)

            # fifo for propagation of end of frame from axi.b channel
            bf = self.bInfoFifo = HandshakedFifo(BFifoIntf)
            bf.DEPTH.set(self.MAX_TRANS_OVERLAP)

    def axiAwHandler(self, wErrFlag):
        req = self.driver.req
        aw = self.a
        r = self._reg

        self.axiAddrDefaults()

        wInfo = self.writeInfoFifo.dataIn
        if self.useTransSplitting():
            LEN_MAX = mask(aw.len._dtype.bit_length())

            lastReqDispatched = r("lastReqDispatched", defVal=1)
            lenDebth = r("lenDebth", req.len._dtype)
            addrBackup = r("addrBackup", req.addr._dtype)
            req_idBackup = r("req_idBackup", req.id._dtype)
            _id = self._sig("id", aw.id._dtype)

            If(lastReqDispatched,
                _id ** req.id,
                aw.addr ** req.addr,
                connect(req.len, aw.len, fit=True),

                req_idBackup ** req.id,
                addrBackup ** (req.addr + self.getBurstAddrOffset()),
                lenDebth ** (req.len - (LEN_MAX + 1)),
                If(wInfo.rd & aw.ready & req.vld,
                    If(req.len > LEN_MAX,
                       lastReqDispatched ** 0 
                    ).Else(
                       lastReqDispatched ** 1 
                    )
                ),
                streamSync(masters=[req],
                           slaves=[aw, wInfo],
                           extraConds={aw: [~wErrFlag]}),
            ).Else(
                _id ** req_idBackup,
                aw.addr ** addrBackup,
                connect(lenDebth, aw.len, fit=True),

                streamSync(slaves=[aw, wInfo], extraConds={aw:[~wErrFlag]}),

                req.rd ** 0,

                If(wInfo.rd & aw.ready,
                   addrBackup ** (addrBackup + self.getBurstAddrOffset()),
                   lenDebth ** (lenDebth - LEN_MAX),
                   If(lenDebth <= LEN_MAX,
                      lastReqDispatched ** 1
                   )
                )
            )
            aw.id ** _id
            wInfo.id ** _id

        else:
            aw.id ** req.id
            wInfo.id ** req.id
            aw.addr ** req.addr
            connect(req.len, aw.len, fit=True)
            streamSync(masters=[req], slaves=[aw, wInfo])

    def axiWHandler(self, wErrFlag):
        w = self.w
        wIn = self.driver.w

        wInfo = self.writeInfoFifo.dataOut
        bInfo = self.bInfoFifo.dataIn

        w.id ** wInfo.id
        w.data ** wIn.data
        w.strb ** wIn.strb

        if self.useTransSplitting():
            wordCntr = self._reg("wWordCntr", self.a.len._dtype, 0)
            doSplit = wordCntr._eq(self.getAxiLenMax()) | wIn.last

            If(streamAck([wInfo, wIn], [bInfo, w]),
               If(doSplit,
                   wordCntr ** 0
               ).Else(
                   wordCntr ** (wordCntr + 1)
               )
            )
            extraConds = {wInfo: [doSplit],
                          bInfo: [doSplit],
                          w: [~wErrFlag]}
            
            w.last ** doSplit

        else:
            w.last ** wIn.last
            extraConds = {wInfo: [wIn.last],
                          bInfo: [wIn.last],
                          w: [~wErrFlag]}

        bInfo.isLast ** wIn.last
        streamSync(masters=[wIn, wInfo],
                   slaves=[bInfo, w],
                   extraConds=extraConds
                   )

    def axiBHandler(self):
        wErrFlag = self._reg("wErrFlag", defVal=0)
        b = self.b
        ack = self.driver.ack
        lastFlags = self.bInfoFifo.dataOut

        If(lastFlags.vld & ack.rd & b.valid & (b.resp != RESP_OKAY),
           wErrFlag ** 1
        )

        self.errorWrite ** wErrFlag 
        ack.data ** b.id
        streamSync(masters=[b, lastFlags],
                   slaves=[ack],
                   extraConds={
                               ack: [lastFlags.isLast]
                               })

        return wErrFlag

    def _impl(self):
        propagateClkRstn(self)

        wErrFlag = self.axiBHandler()
        self.axiAwHandler(wErrFlag)
        self.axiWHandler(wErrFlag)

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = Axi_wDatapump()
    print(toRtl(u))
