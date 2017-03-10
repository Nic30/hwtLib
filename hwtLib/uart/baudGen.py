#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.code import If, log2ceil, isPow2
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam


class UartBaudGen(Unit):
    def _config(self):
        self.FREQ = Param(int(100e6))
        self.BAUD = Param(115200)
        # needs to be a power of 2
        # we oversample the line at a fixed rate to capture each RxD data bit at the "right" time
        # 8 times oversampling by default, use 16 for higher quality reception
        self.OVERSAMPLING = Param(16)
        
    def _declr(self):
        addClkRstn(self)
        self.bitTick = Signal()
            
    def _impl(self):
        baud = evalParam(self.BAUD).val
        freq = evalParam(self.FREQ).val
        oversampling = evalParam(self.OVERSAMPLING).val

        assert isPow2(oversampling) and oversampling > 0
        assert freq > (baud * oversampling)
        
        
        cntrMax = freq // (baud * oversampling)
        cntr = self._reg("cntr", vecT(log2ceil(cntrMax)+ 1, signed=False), 0)
        If(cntr._eq(cntrMax-1),
            self.bitTick ** 1,
            cntr ** 0
        ).Else(
            self.bitTick ** 0,
            cntr ** (cntr + 1)
        )
       
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(UartBaudGen()))
