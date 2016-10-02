#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.bitmask import mask
from hdl_toolkit.hdlObjects.specialValues import DIRECTION
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.agents.handshaked import HandshakedAgent
from hdl_toolkit.interfaces.std import Handshaked, Signal, HandshakeSync
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil, propagateClkRstn
from hdl_toolkit.synthesizer.codeOps import If, Switch, connect
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.interfaces.amba import (Axi4_r, Axi4_addr, AxiStream,
                                    AxiStream_withUserAndStrb)
from hwtLib.interfaces.amba_constants import (BURST_INCR, CACHE_DEFAULT,
                                              LOCK_DEFAULT, PROT_DEFAULT,
                                              QOS_DEFAULT, BYTES_IN_TRANS,
                                              RESP_OKAY)


class AddrSizeHsAgent(HandshakedAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.read
        
        addr = r(intf.addr)
        _len = r(intf.len)
        rem = r(intf.rem)
        user = r(intf.user)
        
        return (addr, _len, rem, user)

    def mkReq(self, addr, _len, rem=0, user=0):
        return (addr, _len, rem, user)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.w
        
        if data is None:
            data = [None for _ in range(4)]

        addr, _len, rem, user = data
        
        w(addr, intf.addr)
        w(_len, intf.len)
        w(rem, intf.rem)
        w(user, intf.user)
        
    
    
class AddrSizeHs(Handshaked):
    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.MAX_LEN = Param(4096 // 8 - 1)
        self.DATA_WIDTH = Param(64)
        self.USER_WIDTH = Param(2)  
    
    def _declr(self):
        self.addr = Signal(dtype=vecT(self.ADDR_WIDTH))
        #  len is number of words -1
        self.len = Signal(dtype=vecT(log2ceil(self.MAX_LEN)))
        
        # rem is number of bits in last word which is valid - 1
        self.rem = Signal(dtype=vecT(log2ceil(self.DATA_WIDTH // 8)))

        # signal of generic purpose
        if evalParam(self.USER_WIDTH).val > 0:
            self.user = Signal(dtype=vecT(self.USER_WIDTH)) 
        
        self.vld = Signal()
        self.rd = Signal(masterDir=DIRECTION.IN)
    
    def _getSimAgent(self):
        return AddrSizeHsAgent

class TransEndInfo(HandshakeSync):
    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.USER_WIDTH = Param(0)  
    
    def _declr(self):
        # rem is number of bits in last word which is valid - 1
        self.rem = Signal(dtype=vecT(log2ceil(self.DATA_WIDTH // 8)))

        # signal of generic purpose
        if evalParam(self.USER_WIDTH).val > 0:
            self.user = Signal(dtype=vecT(self.USER_WIDTH))  
        
        self.propagateLast = Signal()
        HandshakeSync._declr(self)

class Axi4_RDataPump(Unit):
    """
    Foward req to axi ar channel 
    and collect data to data channel form axi r channel 
    
    This unit simplifies axi interface,
    blocks data channel when there is no request pending
    and contains frame merging logic if is required
    
    if req len is wider transaction is internally splited to multiple
    transactions, but readed data are single packet as requested 
    
    rErrFlag stays high when there was error on axi r channel
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
                if self.useUserSig():
                    self.rOut = AxiStream_withUserAndStrb()
                else:
                    self.rOut = AxiStream()
                
                self.rErrFlag = Signal()
        
        with self._paramsShared():
            f = self.sizeRmFifo = HandshakedFifo(TransEndInfo)
            f.DEPTH.set(self.MAX_TRANS_OVERLAP)
    
    def getSizeAlignBits(self):
        return log2ceil(self.DATA_WIDTH // 8).val
    
    def useTransSplitting(self):
        return self.req.len._dtype.bit_length() > self.ar.len._dtype.bit_length()
    
    def useUserSig(self):
        return evalParam(self.req.USER_WIDTH).val > 0
    
    def getBurstAddrOffset(self):
        LEN_MAX = mask(self.ar.len._dtype.bit_length())
        return (LEN_MAX + 1) << self.getSizeAlignBits()
    
    def addrHandler(self, addRmSize):
        ar = self.ar
        req = self.req


        canStartNew = addRmSize.rd
        
        ar.id ** self.DEFAULT_ID
        ar.burst ** BURST_INCR
        ar.cache ** CACHE_DEFAULT
        ar.lock ** LOCK_DEFAULT
        ar.prot ** PROT_DEFAULT
        ar.qos ** QOS_DEFAULT
        ar.size ** BYTES_IN_TRANS(evalParam(self.DATA_WIDTH).val)

        # if axi len is smaller we have to use transaction splitting
        if self.useTransSplitting(): 
            LEN_MAX = mask(ar.len._dtype.bit_length())
            
               
            lastReqDispatched = self._reg("lastReqDispatched", defVal=1) 
            lenDebth = self._reg("lenDebth", req.len._dtype)
            remBackup = self._reg("remBackup", req.rem._dtype)
            rAddr = self._reg("r_addr", req.addr._dtype)
            
            if self.useUserSig():
                user = self._reg("user", self.req.user._dtype)
                If(lastReqDispatched,
                    user ** req.user,
                    addRmSize.user ** req.user 
                ).Else(
                    addRmSize.user ** user
                )
                
            reqLen = self._sig("reqLen", req.len._dtype)
            reqRem = self._sig("reqRem", req.rem._dtype)
            ack = self._sig("ar_ack")
            
            
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
                    lenDebth ** (reqLen - LEN_MAX),
                    lastReqDispatched ** 0
                ).Else(
                    lastReqDispatched ** 1
                )
            )
            
            If(lastReqDispatched,
               ar.valid ** (req.vld & canStartNew),
               ar.addr ** req.addr,
               rAddr ** req.addr,
               
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
                  rAddr ** (rAddr + self.getBurstAddrOffset()) 
               ),
               addRmSize.vld ** ar.ready
            )
        else:
            # if axi len is wider we can directly translate requests to axi
            ar.valid ** (req.vld & canStartNew)
            ar.addr ** req.addr
            connect(req.len, ar.len, fit=True)

            addRmSize.rem ** req.rem
            addRmSize.propagateLast ** 1
            if self.useUserSig():
                addRmSize.user ** req.user
            addRmSize.vld ** (req.vld & ar.ready)
        
    
    def remSizeToStrb(self, remSize, strb):
        strbBytes = 2 ** self.getSizeAlignBits()
        
        Switch(remSize)\
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
        self.rErrFlag ** rErrFlag
        
        
        rOut.data ** r.data
        rOut.last ** (r.last & rmSizeOut.propagateLast)
        
        if self.useUserSig():
            rOut.user ** rmSizeOut.user
        
        self.remSizeToStrb(rmSizeOut.rem, rOut.strb)
        
        rOut.valid ** (r.valid & rmSizeOut.vld)
        r.ready ** (rOut.ready & rmSizeOut.vld)
        rmSizeOut.rd ** (r.valid & r.last & rOut.ready)
        
    def _impl(self):
        propagateClkRstn(self)
        
        self.addrHandler(self.sizeRmFifo.dataIn)
        self.dataHandler(self.sizeRmFifo.dataOut)

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = Axi4_RDataPump()
    print(toRtl(u))
    
