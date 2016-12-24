#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.types.enum import Enum
from hwt.hdlObjects.types.typeCast import toHVal
from hwt.interfaces.utils import addClkRstn
from hwt.code import If, c, FsmBuilder, Switch
from hwt.synthesizer.param import evalParam
from hwtLib.abstract.addrSpace import AddrSpaceItem
from hwtLib.abstract.busConverter import BusConverter
from hwtLib.interfaces.ipif import IPIF


class IpifConverter(BusConverter):
    """
    IPIF converter generator
    byte enable and register clock enable signals are ignored
    """
    def _config(self):
        IPIF._config(self)

    def _declr(self):
        addClkRstn(self)
        
        with self._paramsShared():
            self.bus = IPIF()
            
        self.decorateWithConvertedInterfaces()
        
    def _impl(self):
        DW_B = evalParam(self.DATA_WIDTH).val // 8 
        # build read data output mux
        def isMyAddr(addrSig, addr, size):
            return (addrSig >= addr) & (addrSig < (toHVal(addr) + (size * DW_B)))
        
        st_t = Enum('st_t', ['idle', "writeAck", 'readDelay', 'rdData'])
        ipif = self.bus
        addr = ipif.bus2ip_addr
        ipif.ip2bus_error ** 0
        addrVld = ipif.bus2ip_cs
        
        isInMyAddrSpace = (addr >= self.getMinAddr()) & (addr <= self.getMaxAddr())
        
        st = FsmBuilder(self, st_t)\
        .Trans(st_t.idle,
            (addrVld & isInMyAddrSpace & ipif.bus2ip_rnw, st_t.readDelay),
            (addrVld & isInMyAddrSpace & ~ipif.bus2ip_rnw, st_t.writeAck)
        ).Trans(st_t.writeAck,
            st_t.idle    
        ).Trans(st_t.readDelay,
            st_t.rdData
        ).Trans(st_t.rdData,
            st_t.idle
        ).stateReg
        
        wAck = st._eq(st_t.writeAck)
        ipif.ip2bus_rdack ** st._eq(st_t.rdData)
        ipif.ip2bus_wrack ** wAck
        
        dataToBus = ipif.ip2bus_data ** None     
        for ai in reversed(self._bramPortMapped):
            # map addr for bram ports
            _isMyAddr = isMyAddr(addr, ai.addr, ai.size)
            
            a = self._sig("addr_forBram_" + ai.port._name, ipif.bus2ip_addr._dtype)
            a ** (addr - ai.addr)
            
            addrHBit = ai.port.addr._dtype.bit_length()
            if ai.alignOffsetBits:
                bitForAligig = ai.alignOffsetBits
                assert addrHBit + bitForAligig <= evalParam(self.ADDR_WIDTH).val
                c(a[(addrHBit + bitForAligig):bitForAligig], ai.port.addr, fit=True)
            else:
                c(a[addrHBit:], ai.port.addr, fit=True)
                
            ai.port.en ** _isMyAddr
            ai.port.we ** (_isMyAddr & wAck)
            
            dataToBus = If(_isMyAddr,
                ipif.ip2bus_data ** ai.port.dout
            ).Else(
                dataToBus
            )
            
            ai.port.din ** ipif.bus2ip_data


        
        for ai in   self._directlyMapped:
            ai.port.dout.vld ** (addr._eq(ai.addr) & ~ipif.bus2ip_rnw & wAck)
            ai.port.dout.data ** ipif.bus2ip_data
        
        _isInBramFlags = []
        Switch(ipif.bus2ip_addr)\
        .addCases(
                [(ai.addr, ipif.ip2bus_data ** ai.port.din) 
                 for ai in   self._directlyMapped]
        ).Default(
            dataToBus
        )
        

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    # u = IpifConverter([(i * 4 , "data%d" % i) for i in range(2)] + 
    #                  [(3 * 4, "bramMapped", 32)])
    #
    u = IpifConverter([(i * 4 , "data%d" % i) for i in range(2)] + 
                      [AddrSpaceItem(3 * 4, "bramMapped", 32, 2)])
    
    print(toRtl(u))
    
