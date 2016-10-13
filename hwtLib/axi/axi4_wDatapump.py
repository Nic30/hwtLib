#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.bitmask import mask
from hdl_toolkit.interfaces.std import Signal, Handshaked, VectSignal, \
    HandshakeSync
from hdl_toolkit.interfaces.utils import propagateClkRstn
from hdl_toolkit.synthesizer.codeOps import connect, If
from hdl_toolkit.synthesizer.param import Param
from hwtLib.axi.axi_datapump_base import Axi_datapumpBase
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.interfaces.amba import Axi4_w, AxiStream, Axi4_b
from hwtLib.interfaces.amba_constants import RESP_OKAY


def axiHsAck(m, s):
    return m.valid & s.ready

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

        
class Axi4_wDatapump(Axi_datapumpBase):

    def _declr(self):
        super()._declr() # add clk, rst, axi addr channel and req channel
        with self._asExtern():
            with self._paramsShared():
                self.w = Axi4_w()
                self.b = Axi4_b()

                self.wIn = AxiStream()
                
                self.errorWrite = Signal()
            self.reqAck = Handshaked()
            self.reqAck.DATA_WIDTH.set(self.ID_WIDTH)
            
        with self._paramsShared():
            # fifo for id propagation and frame splitting on axi.w channel 
            wf = self.writeInfoFifo = HandshakedFifo(WFifoIntf)
            wf.ID_WIDTH.set(self.ID_WIDTH)
            wf.DEPTH.set(self.MAX_TRANS_OVERLAP)
            
            # fifo for propagation of end of frame from axi.b channel
            bf = self.bInfoFifo = HandshakedFifo(BFifoIntf)
            bf.DEPTH.set(self.MAX_TRANS_OVERLAP)
            

    def axiAwHandler(self):
        req = self.req
        aw = self.a

        self.axiAddrDefaults()

        if self.useTransSplitting():
            LEN_MAX = mask(aw.len._dtype.bit_length())
            wInfo = self.writeInfoFifo.dataIn
            
            lastReqDispatched = self._reg("lastReqDispatched", defVal=1)
            lenDebth = self._reg("lenDebth", req.len._dtype)
            addrBackup = self._reg("addrBackup", req.addr._dtype)
            req_idBackup = self._reg("req_idBackup", self.req.id._dtype)
            _id = self._sig("id", aw.id._dtype)
                    
            en = wInfo.rd
            
            If(lastReqDispatched,
                _id ** req.id,
                aw.addr ** req.addr,
                connect(req.len, aw.len, fit=True),
                aw.valid ** (en & req.vld),

                wInfo.vld ** (req.vld & aw.ready),
                
                req.rd ** (wInfo.rd & aw.ready),
                
                req_idBackup ** req.id,
                addrBackup ** (req.addr + self.getBurstAddrOffset()),
                lenDebth ** (req.len - (LEN_MAX + 1)),
                If(en & (req.len > LEN_MAX) & aw.ready & req.vld,
                   lastReqDispatched ** 1 
                )
            ).Else(
                _id ** req_idBackup,
                aw.addr ** addrBackup,
                connect(lenDebth, aw.len, fit=True),
                aw.valid ** en,
                
                wInfo.vld ** aw.ready,
                req.rd ** 0,
                
                If(en & aw.ready,
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
            aw.addr ** req.addr
            connect(req.len, aw.len, fit=True)
            aw.valid ** req.vld 
            req.rd ** aw.ready
            

    
    def axiWHandler(self):
        w = self.w
        wIn = self.wIn
        wInfo = HsBuilder(self, self.writeInfoFifo.dataOut).reg().end
        bInfo = self.bInfoFifo.dataIn
        
        enable = wInfo.vld & bInfo.rd
        
        w.id ** wInfo.id
        w.data ** wIn.data
        w.strb ** wIn.strb
        
        if self.useTransSplitting():
            wordCntr = self._reg("wWordCntr", self.a.len._dtype, 0)
            doSplit = wordCntr._eq(self.getAxiLenMax())
            
            If(enable & axiHsAck(wIn, w),
               If(wIn.last,
                   wordCntr ** 0
               ).Else(
                   wordCntr ** (wordCntr + 1)
               )
            )
            wInfo.rd ** (axiHsAck(wIn, w) & (doSplit | wIn.last) & bInfo.rd)
            bInfo.isLast ** wIn.last
            bInfo.vld ** (axiHsAck(wIn, w) & (doSplit | wIn.last) & wInfo.vld)
            
            w.last ** (doSplit | wIn.last)
            w.valid ** (enable & wIn.valid)
            wIn.ready ** (enable & w.ready)

        else:
            w.last ** wIn.last
            w.valid ** (enable & wIn.valid)
            wIn.ready ** w.ready
            
    def axiBHandler(self):
        wErrFlag = self._reg("wErrFlag", defVal=0)
        b = self.b
        reqAck = self.reqAck
        
        lastFlags = HsBuilder(self, self.bInfoFifo.dataOut).reg().end
        
        If(lastFlags.vld & reqAck.rd & b.valid & (b.resp != RESP_OKAY),
           wErrFlag ** 1
        )

        self.errorWrite ** wErrFlag 
        b.ready ** (lastFlags.vld & reqAck.rd)
        lastFlags.rd ** (reqAck.rd & b.valid) 
        
        reqAck.vld ** (lastFlags.vld & lastFlags.isLast & b.valid)
        reqAck.data ** b.id
        
    
    def _impl(self):
        propagateClkRstn(self)
        
        self.axiAwHandler()
        self.axiWHandler()
        self.axiBHandler()
        
        
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = Axi4_wDatapump()
    print(toRtl(u))
