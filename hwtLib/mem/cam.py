#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT, hBit
from hwt.hdlObjects.types.array import Array
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, VldSynced, Signal
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.constants import SERI_MODE
from hwt.code import If, Concat, log2ceil
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam


class AddrDataHsAgent(HandshakedAgent):
    def doWrite(self, s, data):
        i = self.intf
        w = s.write 
        if data is None:
            addr, d, mask = None, None, None
        else: 
            addr, d, mask = data
        
        w(addr, i.addr)
        w(d, i.data)
        w(mask, i.mask)
        
    def doRead(self, s):
        i = self.intf
        r = s.read
        return r(i.addr), r(i.data), r(i.mask)
        
class AddrDataHs(Handshaked):
    def _config(self):
        Handshaked._config(self)
        self.ADDR_WIDTH = Param(4)
        
    def _declr(self):
        Handshaked._declr(self)
        self.addr = Signal(dtype=vecT(self.ADDR_WIDTH))
        self.mask = Signal(dtype=vecT(self.DATA_WIDTH))

    def _getSimAgent(self):
        return AddrDataHsAgent


class Cam(Unit):
    """
    Content addressable memory
    
    Simple combinational version

    MATCH_LATENCY = 1
    """
    _serializerMode = SERI_MODE.PARAMS_UNIQ
    
    def _config(self):
        self.DATA_WIDTH = Param(36)
        self.ITEMS = Param(16)
        
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.match = Handshaked()
            self.write = AddrDataHs()
            self.write.ADDR_WIDTH.set(log2ceil(self.ITEMS - 1))
        self.out = VldSynced()
        self.out._replaceParam("DATA_WIDTH", self.ITEMS)
    
    
    def writeHandler(self, mem):
        w = self.write
        w.rd ** 1
        
        If(self.clk._onRisingEdge() & w.vld,
           mem[w.addr] ** Concat(w.data, w.mask[0])
        )
        
    def matchHandler(self, mem):
        key = self.match
        
        out = self._reg("out_reg", self.out.data._dtype, defVal=0)
        outNext = out.next
        outVld = self._reg("out_vld_reg", defVal=0)
        
        key.rd ** 1
        outVld ** key.vld
        
        for i in range(evalParam(self.ITEMS).val):
            outNext[i] ** mem[i]._eq(Concat(key.data , hBit(1)))
        
        self.out.data ** out
        self.out.vld ** outVld 
        
    
    def _impl(self):
        # +1 bit to validity check
        self._mem = self._sig("cam_mem", Array(vecT(self.DATA_WIDTH + 1), self.ITEMS),
                                         [0 for _ in range(evalParam(self.ITEMS).val)]) 
        self.writeHandler(self._mem)
        self.matchHandler(self._mem)
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = Cam()
    print(toRtl(u))  
