#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.array import Array
from hwt.interfaces.std import BramPort, Clk, BramPort_withoutClk
from hwt.serializer.constants import SERI_MODE
from hwt.code import If, power
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam


class RamSingleClock(Unit):
    _serializerMode = SERI_MODE.PARAMS_UNIQ
    
    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.ADDR_WIDTH = Param(4)
        self.PORT_CNT = Param(1)
        
    def _declr(self):
        PORTS = evalParam(self.PORT_CNT).val
        
        with self._paramsShared():
            self.clk = Clk()
            self.a = BramPort_withoutClk()
            for i in range(PORTS - 1):
                name = self.genPortName(i + 1)
                setattr(self, name, BramPort_withoutClk()) 
                
    @staticmethod            
    def genPortName(index):
        return chr(ord('a') + index)
        
    def connectPort(self, port, mem):
        If(self.clk._onRisingEdge() & port.en,
           If(port.we,
              mem[port.addr] ** port.din
           ),
           port.dout ** mem[port.addr]
        )
        
    def _impl(self):
        PORTS = evalParam(self.PORT_CNT).val
        dt = Array(vecT(self.DATA_WIDTH), power(2, self.ADDR_WIDTH))
        self._mem = self._sig("ram_memory", dt)
        
        for i in range(PORTS):
            self.connectPort(getattr(self, self.genPortName(i)), self._mem)
        
        
class Ram_sp(Unit):
    """
    Write first variant
    """
    _serializerMode = SERI_MODE.PARAMS_UNIQ
    
    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.ADDR_WIDTH = Param(4)
    
    def _declr(self):
        with self._paramsShared():
            self.a = BramPort()
    
    def connectPort(self, port, mem):
        If(port.clk._onRisingEdge() & port.en,
           If(port.we,
              mem[port.addr] ** port.din
           ),
           port.dout ** mem[port.addr]
        )
        
    def _impl(self):
        dt = Array(vecT(self.DATA_WIDTH), power(2, self.ADDR_WIDTH))
        self._mem = self._sig("ram_memory", dt)
        
        self.connectPort(self.a, self._mem)

class Ram_dp(Ram_sp):
    def _declr(self):
        super()._declr()
        with self._paramsShared():
            self.b = BramPort()

    def _impl(self):
        super()._impl()
        self.connectPort(self.b, self._mem)

def getRamCls(noOfPorts):
    if noOfPorts == 1:
        return Ram_sp
    elif noOfPorts == 2:
        return Ram_dp
    else:
        raise NotImplementedError() 

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(Ram_dp()))
