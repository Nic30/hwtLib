#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.enum import Enum
from hwt.interfaces.utils import addClkRstn
from hwt.code import FsmBuilder, If, In, Switch, log2ceil
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.interfaces.amba import AxiLite
from hwtLib.interfaces.ipif import IPIF


class AxiLiteIpifConv(Unit):
    """
    [TODO] not finished
    """
    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)
        self.TIMEOUT = Param(511)

    def _declr(self):
        with self._paramsShared():
            addClkRstn(self)
            self.axi = AxiLite()
            self.ipif = IPIF()
    
    def timeoutIncrementLogic(self, st, timeoutCntr):
        stT = st._dtype
        If(st._eq(stT.idle),
            timeoutCntr ** 0
        ).Elif(In(st, [stT.read, stT.write]),
            timeoutCntr ** (timeoutCntr+1)
        )
        
    def _impl(self):
        axi = self.axi
        ipif = self.ipif
        stT= Enum("stT", ["idle", 
                          "read",
                          "readAxiResp",
                          "readAxiErrResp",
                          "writeAxiData",
                          "write",
                          "writeAxiResp",
                          "writeAxiErrResp"])
        timeoutCntr = self._reg("timeoutCntr", vecT(log2ceil(self.TIMEOUT), signed=False))   
        timeout = timeoutCntr._eq(self.TIMEOUT)
        readReg = self._reg("read_reg", vecT(self.DATA_WIDTH))
        wAddr = self._reg("write_addr_reg", vecT(self.ADDR_WIDTH))
        
        writeReg = self._reg("write_reg", vecT(self.DATA_WIDTH))
    
        
        st = FsmBuilder(self, stT)\
        .Trans(stT.idle,
            (axi.ar.valid, stT.read),
            (axi.aw.valid, stT.writeAxiData)
            
        ).Trans(stT.read,
            (ipif.ip2bus_rdack, stT.readAxiResp),
            (timeout,           stT.readAxiErrResp)
            
        ).Trans(stT.readAxiResp,
            (axi.r.ready, stT.idle) 
            
        ).Trans(stT.writeAxiData,
            (axi.w.valid, stT.write)
            
        ).Trans(stT.write,
            (ipif.ip2bus_wrack, stT.writeAxiResp),
            (timeout, stT.writeAxiErrResp)
            
        ).Trans(stT.writeAxiResp,
            (axi.b.ready, stT.idle)
            
        ).Trans(stT.writeAxiErrResp,
            (axi.b.ready, stT.idle)
            
        ).stateReg

        If(st._eq(stT.idle) & axi.aw.valid,
            wAddr ** axi.aw.addr
        )

        Switch(st)\
        .Case(stT.idle,
            ipif.bus2ip_addr ** axi.ar.addr
        ).Case(stT.write,
            ipif.bus2ip_addr ** wAddr
        ).Default(
            ipif.bus2ip_addr ** None
        )
        
        If(ipif.ip2bus_rdack,
           readReg ** ipif.ip2bus_data
        )

        If(axi.w.valid & st._eq(stT.writeAxiData),
            writeReg** axi.w.data
        )
        
        self.timeoutIncrementLogic(st, timeoutCntr)
        

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiLiteIpifConv()
    print(toRtl(u))