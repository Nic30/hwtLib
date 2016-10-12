#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.bitmask import mask
from hdl_toolkit.interfaces.agents.handshaked import HandshakedAgent
from hdl_toolkit.interfaces.std import Handshaked, Signal, HandshakeSync, \
    VectSignal
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil, propagateClkRstn
from hdl_toolkit.synthesizer.codeOps import If, Switch, connect
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.interfaces.amba import (Axi4_r, Axi4_addr, AxiStream_withId)
from hwtLib.interfaces.amba_constants import (BURST_INCR, CACHE_DEFAULT,
                                              LOCK_DEFAULT, PROT_DEFAULT,
                                              QOS_DEFAULT, BYTES_IN_TRANS,
                                              RESP_OKAY)


class AddrSizeHsAgent(HandshakedAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.read
        
        _id = r(intf.id)
        addr = r(intf.addr)
        _len = r(intf.len)
        rem = r(intf.rem)
        
        return (_id, addr, _len, rem)

    def mkReq(self, addr, _len, rem=0, _id=0):
        return (_id, addr, _len, rem)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.w
        
        if data is None:
            data = [None for _ in range(4)]

        _id, addr, _len, rem = data
        
        w(_id, intf.id)
        w(addr, intf.addr)
        w(_len, intf.len)
        w(rem, intf.rem)
    
class AddrSizeHs(Handshaked):
    def _config(self):
        self.ID_WIDTH = Param(4)
        self.ADDR_WIDTH = Param(32)
        self.MAX_LEN = Param(4096 // 8 - 1)
        self.DATA_WIDTH = Param(64)
    
    def _declr(self):
        self.id = VectSignal(self.ID_WIDTH)
        
        self.addr = VectSignal(self.ADDR_WIDTH)
        #  len is number of words -1
        self.len = VectSignal(log2ceil(self.MAX_LEN))
        
        # rem is number of bits in last word which is valid - 1
        self.rem = VectSignal(log2ceil(self.DATA_WIDTH // 8))

        HandshakeSync._declr(self)
    
    def _getSimAgent(self):
        return AddrSizeHsAgent

class TransEndInfo(HandshakeSync):
    def _config(self):
        self.DATA_WIDTH = Param(64)
    
    def _declr(self):
        # rem is number of bits in last word which is valid - 1
        self.rem = VectSignal(log2ceil(self.DATA_WIDTH // 8))

        self.propagateLast = Signal()
        HandshakeSync._declr(self)

class Axi4_rDataPump(Unit):
    """
    Foward req to axi ar channel 
    and collect data to data channel form axi r channel 
    
    This unit simplifies axi interface,
    blocks data channel when there is no request pending
    and contains frame merging logic if is required
    
    if req len is wider transaction is internally splited to multiple
    transactions, but readed data are single packet as requested 
    
    errorRead stays high when there was error on axi r channel
    it will not affect unit functionality
    """
    
    def _config(self):
        self.DEFAULT_ID = Param(0)
        self.MAX_TRANS_OVERLAP = Param(16)
        self.MAX_LEN = Param(4096 // 8 - 1)
        
        self.ID_WIDTH = Param(4)
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.USER_WIDTH = Param(2)  # if 0 is used user signal completly disapears
    
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.ar = Axi4_addr()
                self.r = Axi4_r()
                
                # user flag from req will be set in every word on output rOut 
                self.req = AddrSizeHs()
                self.rOut = AxiStream_withId()
                
                self.errorRead = Signal()
        
        with self._paramsShared():
            f = self.sizeRmFifo = HandshakedFifo(TransEndInfo)
            f.DEPTH.set(self.MAX_TRANS_OVERLAP)
    
    def getSizeAlignBits(self):
        return log2ceil(self.DATA_WIDTH // 8).val
    
    def useTransSplitting(self):
        return self.req.len._dtype.bit_length() > self.ar.len._dtype.bit_length()
    
    def getBurstAddrOffset(self):
        LEN_MAX = mask(self.ar.len._dtype.bit_length())
        return (LEN_MAX + 1) << self.getSizeAlignBits()
    
    def arIdHandler(self, lastReqDispatched):
        req_idBackup = self._reg("req_idBackup", self.req.id._dtype)
        If(lastReqDispatched,
            req_idBackup ** self.req.id,
            self.ar.id ** self.req.id 
        ).Else(
            self.ar.id ** req_idBackup
        )
        
    def addrHandler(self, addRmSize):
        ar = self.ar
        req = self.req
        canStartNew = addRmSize.rd
         
        ar.burst ** BURST_INCR
        ar.cache ** CACHE_DEFAULT
        ar.lock ** LOCK_DEFAULT
        ar.prot ** PROT_DEFAULT
        ar.qos ** QOS_DEFAULT
        ar.size ** BYTES_IN_TRANS(evalParam(self.DATA_WIDTH).val)

        # if axi len is smaller we have to use transaction splitting
        if self.useTransSplitting(): 
            LEN_MAX = mask(ar.len._dtype.bit_length())
            ADDR_STEP = self.getBurstAddrOffset()
            
               
            lastReqDispatched = self._reg("lastReqDispatched", defVal=1) 
            lenDebth = self._reg("lenDebth", req.len._dtype)
            remBackup = self._reg("remBackup", req.rem._dtype)
            rAddr = self._reg("r_addr", req.addr._dtype)
                           
            reqLen = self._sig("reqLen", req.len._dtype)
            reqRem = self._sig("reqRem", req.rem._dtype)
            ack = self._sig("ar_ack")
            
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
               ar.valid ** (req.vld & canStartNew),
               ar.addr ** req.addr,
               rAddr ** (req.addr + ADDR_STEP),
               
               req.rd ** (canStartNew & ar.ready),
               reqLen ** req.len,
               reqRem ** req.rem,
               ack ** (req.vld & canStartNew & ar.ready),
               addRmSize.vld ** (req.vld & ar.ready),
               remBackup ** req.rem,
            ).Else(
               ar.addr ** rAddr,
               ar.valid ** canStartNew,
               req.rd ** 0,
               
               reqLen ** lenDebth,
               reqRem ** remBackup,
               ack ** (canStartNew & ar.ready),
               If(canStartNew & ar.ready,
                  rAddr ** (rAddr + ADDR_STEP) 
               ),
               addRmSize.vld ** ar.ready
            )
        else:
            # if axi len is wider we can directly translate requests to axi
            ar.id ** req.id
            ar.valid ** (req.vld & canStartNew)
            ar.addr ** req.addr

            connect(req.len, ar.len, fit=True)

            addRmSize.rem ** req.rem
            addRmSize.propagateLast ** 1
            addRmSize.vld ** (req.vld & ar.ready)
        
    
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
        rOut = self.rOut
        
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
        rOut.valid ** (r.valid & rmSizeOut.vld)
        r.ready ** (rOut.ready & rmSizeOut.vld)
        rmSizeOut.rd ** (r.valid & r.last & rOut.ready)
        
    def _impl(self):
        propagateClkRstn(self)
        
        self.addrHandler(self.sizeRmFifo.dataIn)
        self.dataHandler(self.sizeRmFifo.dataOut)

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = Axi4_rDataPump()
    print(toRtl(u))
    
