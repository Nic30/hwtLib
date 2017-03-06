#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.bitmask import mask
from hwt.code import If, Switch, connect, log2ceil
from hwt.interfaces.std import Signal, HandshakeSync, VectSignal
from hwt.interfaces.utils import propagateClkRstn
from hwt.synthesizer.param import Param
from hwtLib.amba.axi4 import Axi4_r
from hwtLib.amba.axiDatapumpIntf import AxiRDatapumpIntf
from hwtLib.amba.axi_datapump_base import Axi_datapumpBase
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync


class TransEndInfo(HandshakeSync):
    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        # rem is number of bits in last word which is valid - 1
        self.rem = VectSignal(log2ceil(self.DATA_WIDTH // 8))

        self.propagateLast = Signal()
        HandshakeSync._declr(self)


class Axi_rDatapump(Axi_datapumpBase):
    """
    Foward req to axi ar channel
    and collect data to data channel form axi r channel

    This unit simplifies axi interface,
    blocks data channel when there is no request pending
    and contains frame merging logic if is required

    if req len is wider transaction is internally splited to multiple
    transactions, but read data are single packet as requested

    errorRead stays high when there was error on axi r channel
    it will not affect unit functionality
    \n""" + Axi_datapumpBase.__doc__

    def _declr(self):
        super()._declr()  # add clk, rst, axi addr channel and req channel
        with self._paramsShared():
            self.r = Axi4_r()
            self.driver = AxiRDatapumpIntf()
            self.errorRead = Signal()

            f = self.sizeRmFifo = HandshakedFifo(TransEndInfo)
            f.DEPTH.set(self.MAX_TRANS_OVERLAP)

    def arIdHandler(self, lastReqDispatched):
        a = self.a
        req = self.driver.req
        req_idBackup = self._reg("req_idBackup", req.id._dtype)

        If(lastReqDispatched,
            req_idBackup ** req.id,
            a.id ** req.id 
        ).Else(
            a.id ** req_idBackup
        )

    def addrHandler(self, addRmSize, rErrFlag):
        ar = self.a
        req = self.driver.req
        r, s = self._reg, self._sig

        self.axiAddrDefaults() 

        # if axi len is smaller we have to use transaction splitting
        if self.useTransSplitting():
            LEN_MAX = mask(ar.len._dtype.bit_length())
            ADDR_STEP = self.getBurstAddrOffset()

            lastReqDispatched = r("lastReqDispatched", defVal=1)
            lenDebth = r("lenDebth", req.len._dtype)
            remBackup = r("remBackup", req.rem._dtype)
            rAddr = r("r_addr", req.addr._dtype)

            reqLen = s("reqLen", req.len._dtype)
            reqRem = s("reqRem", req.rem._dtype)

            ack = s("ar_ack")

            self.arIdHandler(lastReqDispatched)
            If(reqLen > LEN_MAX,
               ar.len ** LEN_MAX,
               addRmSize.rem ** 0,
               addRmSize.propagateLast ** 0
            ).Else(
               connect(reqLen, ar.len, fit=True),  # connect only lower bits of len
               addRmSize.rem ** reqRem,
               addRmSize.propagateLast ** 1
            )

            If(ack,
                If(reqLen > LEN_MAX,
                    lenDebth ** (reqLen - (LEN_MAX + 1)),
                    lastReqDispatched ** 0
                ).Else(
                    lastReqDispatched ** 1
                )
            )

            If(lastReqDispatched,
               ar.addr ** req.addr,
               rAddr ** (req.addr + ADDR_STEP),

               reqLen ** req.len,
               reqRem ** req.rem,
               remBackup ** req.rem,
               ack ** (req.vld & addRmSize.rd & ar.ready),
               streamSync(masters=[req],
                          slaves=[addRmSize, ar],
                          extraConds={ar:[~rErrFlag]}),
            ).Else(
               req.rd ** 0,
               ar.addr ** rAddr,
               ack ** (addRmSize.rd & ar.ready),
               If(ack,
                  rAddr ** (rAddr + ADDR_STEP) 
               ),

               reqLen ** lenDebth,
               reqRem ** remBackup,
               streamSync(slaves=[addRmSize, ar],
                          extraConds={ar:[~rErrFlag]}),
            )
        else:
            # if axi len is wider we can directly translate requests to axi
            ar.id ** req.id
            ar.addr ** req.addr

            connect(req.len, ar.len, fit=True)

            addRmSize.rem ** req.rem
            addRmSize.propagateLast ** 1

            streamSync(masters=[req],
                       slaves=[ar, addRmSize],
                       extraConds={ar: [~rErrFlag]})

    def remSizeToStrb(self, remSize, strb):
        strbBytes = 2 ** self.getSizeAlignBits()

        return Switch(remSize)\
                .Case(0,
                      strb ** mask(strbBytes)
                ).addCases(
                 [ (i + 1, strb ** mask(i + 1)) 
                   for i in range(strbBytes - 1)]
                )

    def dataHandler(self, rmSizeOut): 
        r = self.r
        rOut = self.driver.r

        rErrFlag = self._reg("rErrFlag", defVal=0)
        If(r.valid & rOut.ready & (r.resp != RESP_OKAY),
           rErrFlag ** 1
        )
        self.errorRead ** rErrFlag

        rOut.id ** r.id
        rOut.data ** r.data

        If(r.valid & r.last,
            self.remSizeToStrb(rmSizeOut.rem, rOut.strb)
        ).Else(
            rOut.strb ** mask(2 ** self.getSizeAlignBits())
        )
        rOut.last ** (r.last & rmSizeOut.propagateLast)

        streamSync(masters=[r, rmSizeOut],
                   slaves=[rOut],
                   extraConds={rmSizeOut: [r.last],
                               rOut: [~rErrFlag]})

        return rErrFlag

    def _impl(self):
        propagateClkRstn(self)

        rErrFlag = self.dataHandler(self.sizeRmFifo.dataOut)
        self.addrHandler(self.sizeRmFifo.dataIn, rErrFlag)

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = Axi_rDatapump()
    print(toRtl(u))
