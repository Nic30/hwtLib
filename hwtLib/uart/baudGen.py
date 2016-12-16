#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.bitmask import mask
from hdl_toolkit.hdlObjects.typeShortcuts import vecT, hBit
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.interfaces.utils import log2ceil, addClkRstn
from hdl_toolkit.synthesizer.codeOps import If
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam


class UartBaudGen(Unit):
    def _config(self):
        self.FREQ = Param(int(100e6))
        self.BAUD = Param(115200)
        # needs to be a power of 2
        # we oversample the line at a fixed rate to capture each RxD data bit at the "right" time
        # 8 times oversampling by default, use 16 for higher quality reception
        self.OVERSAMPLING = Param(8)
        
    def _declr(self):
        addClkRstn(self)
        self.enable = Signal()
        self.tick = Signal()
            
    def _impl(self):
        baud = evalParam(self.BAUD).val
        freq = evalParam(self.FREQ).val
        oversampling = evalParam(self.OVERSAMPLING).val
        
        accWidth = log2ceil(freq // baud).val + 8  # +/- 2% max timing error over a byte
        # this makes sure Inc calculation doesn't overflow
        shiftLimiter = log2ceil(baud * oversampling >> (31 - accWidth)).val  
        inc = (((baud * oversampling << (accWidth - shiftLimiter))
               + (freq >> (shiftLimiter + 1))) // (freq >> shiftLimiter)
               ) & mask(accWidth + 1) 
        
        acc = self._reg("acc", vecT(accWidth + 1, signed=False), defVal=0)

        If(self.enable,
           acc ** (hBit(0)._concat(acc[accWidth:]) + inc)
        ).Else(
           acc ** inc
        )
        
        self.tick ** acc[accWidth]
        
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(UartBaudGen()))