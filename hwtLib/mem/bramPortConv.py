#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import BramPort_withoutClk
from hwt.code import c, If
from hwt.synthesizer.param import evalParam
from hwtLib.abstract.busConverter import BusConverter
from hwt.hdlObjects.types.array import Array


def inRange(n, lower, size):
    return (n >= lower) & (n < (lower + size))

class BramPortStructEndpoint(BusConverter):
    def _config(self):
        BramPort_withoutClk._config(self)
        
    def _declr(self):
        with self._paramsShared():
            self.bus = BramPort_withoutClk()
        
        assert self._suggestedAddrWidth() <= evalParam(self.ADDR_WIDTH).val
        self.decorateWithConvertedInterfaces()
    
    def _impl(self):
        bus = self.bus
        
        def connectRegIntfAlways(regIntf, _addr):
            return (
                    c(bus.din, regIntf.dout.data) + 
                    c(bus.we & bus.en & bus.addr._eq(_addr), regIntf.dout.vld)
                   )
        
        def connectBramPortAlways(bramPort, addrOffset, size, _addrVld):
            # explicit signal because vhdl cannot index the result of a type conversion
            addr_tmp = self._sig(bramPort._name + "_addr_tmp", vecT(self.ADDR_WIDTH))
            c(bus.addr - addrOffset, addr_tmp)
            
            return (
                c(addr_tmp, bramPort.addr, fit=True) + 
                c(bus.we & _addrVld, bramPort.we) + 
                c(bus.en & _addrVld, bramPort.en) + 
                c(bus.din, bramPort.din))
        
        doutMuxTop = bus.dout ** None

        # reversed to more pretty code        
        for ai in reversed(self._bramPortMapped):
            
            # if we can use prefix instead of addr comparing do it
            tmp = ai.port._addrSpaceItem.getMyAddrPrefix()
            if tmp is None:
                _addrVld = inRange(bus.addr, ai.addr, ai.size)
            else:
                prefix, subaddrBits = tmp
                _addrVld = bus.addr[:subaddrBits]._eq(prefix)
                 
            
            connectBramPortAlways(ai.port, ai.addr, ai.size, _addrVld)
            doutMuxTop = If(_addrVld,
                            bus.dout ** ai.port.dout  
                         ).Else(
                            doutMuxTop
                         )
      
        # reversed to more pretty code
        for ai in reversed(self._directlyMapped):
            connectRegIntfAlways(ai.port, ai.addr)
            
            doutMuxTop = If(bus.addr._eq(ai.addr),
                            bus.dout ** ai.port.din 
                         ).Else(
                            doutMuxTop
                         )
                         

if __name__ == "__main__":
    from hwt.hdlObjects.types.struct import HStruct
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.types.ctypes import uint32_t
    
    u = BramPortStructEndpoint(
            HStruct(
                (uint32_t, "reg0"),
                (uint32_t, "reg1"),
                (Array(uint32_t, 1024), "segment0"),
                (Array(uint32_t, 1024), "segment1"),
                (Array(uint32_t, 1024 + 4), "nonAligned0")
                )
            )
    u.DATA_WIDTH.set(32)
    print(toRtl(u))
