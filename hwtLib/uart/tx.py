#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, log2ceil, Concat
from hwt.hdlObjects.typeShortcuts import vecT, hBit
from hwt.interfaces.std import Handshaked, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.clocking.timers import timers


# http://ece-research.unm.edu/jimp/vhdl_fpgas/slides/UART.pdf
class UartTx(Unit):
    def _config(self):
        self.FREQ = Param(int(100e6))
        self.BAUD = Param(115200)
    
    def _declr(self):
        addClkRstn(self)
        self.dataIn = Handshaked()
        self.dataIn.DATA_WIDTH.set(8)
        self.txd = Signal()
        
    def _impl(self):
        START_BIT = hBit(0)
        STOP_BIT = hBit(1)
        
        propagateClkRstn(self)
        tick = timers(self, [self.FREQ//self.BAUD])[0]
        din = self.dataIn
        
        r = self._reg
        CNTR_MAX = 10
        data = r("data", vecT(CNTR_MAX))  # data + start bit + stop bit
        cntr = r("cntr", vecT(log2ceil(CNTR_MAX), False), CNTR_MAX)
        
        en = r("en")
         
        If(~en & din.vld,
           data ** Concat(STOP_BIT, din.data, START_BIT),
           en ** 1
        ).Elif(tick & en,
           data ** hBit(1)._concat(data[:1]), # sll where 1 is shifted from left
           If(cntr._eq(0),
              en ** 0,
              cntr ** CNTR_MAX
           ).Else(
              cntr ** (cntr - 1)
           )
        )
        din.rd ** ~en
        self.txd ** data[0]
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = UartTx()
    print(toRtl(u)) 
        
