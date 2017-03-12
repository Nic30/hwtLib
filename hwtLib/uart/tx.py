#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat
from hwt.hdlObjects.typeShortcuts import vecT, hBit
from hwt.interfaces.std import Handshaked, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.clocking.clkBuilder import ClkBuilder


# http://ece-research.unm.edu/jimp/vhdl_fpgas/slides/UART.pdf
class UartTx(Unit):
    def _config(self):
        self.FREQ = Param(int(100e6))
        self.BAUD = Param(115200)
        #self.PARITY = Param(None)

    def _declr(self):
        addClkRstn(self)
        self.dataIn = Handshaked()
        self.dataIn.DATA_WIDTH.set(8)
        self.txd = Signal()
        
    def _impl(self):
        propagateClkRstn(self)
        START_BIT = hBit(0)
        STOP_BIT = hBit(1)
        r = self._reg
        CNTR_MAX = 10
        BIT_RATE = self.FREQ // self.BAUD

        din = self.dataIn

        data = r("data", vecT(CNTR_MAX))  # data + start bit + stop bit
        en = r("en")
        tick, last = ClkBuilder(self, self.clk).timers(
                                                       [BIT_RATE, BIT_RATE * CNTR_MAX],
                                                       en)

        If(~en & din.vld,
           data ** Concat(STOP_BIT, din.data, START_BIT),
           en ** 1
        ).Elif(tick & en,
           data ** hBit(1)._concat(data[:1]),  # sll where 1 is shifted from left
           If(last,
              en ** 0,
           )
        )
        din.rd ** ~en
        
        txd = r("reg_rxd", defVal=1)
        If(tick,
           txd ** data[0]
        )
        self.txd ** txd
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = UartTx()
    print(toRtl(u)) 
        
