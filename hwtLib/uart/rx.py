#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal, VldSynced
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.clocking.clkBuilder import ClkBuilder


class UartRx(Unit):
    def _config(self):
        self.FREQ = Param(int(100e6))
        self.BAUD = Param(115200)
        self.OVERSAMPLING = Param(16)
        
    def _declr(self):
        addClkRstn(self)

        self.dataOut = VldSynced()
        self.dataOut.DATA_WIDTH.set(8)

        self.rxd = Signal()
    
    def _impl(self):
        START_BIT = 0
        STOP_BIT = 1
        
        os = evalParam(self.OVERSAMPLING).val
        baud = evalParam(self.BAUD).val
        freq = evalParam(self.FREQ).val
        assert freq >= baud * os, "Frequency too low for current Baud rate and oversampling"
        assert os >= 8 and (os & (os - 1)) == 0, "Invalid oversampling value"

        propagateClkRstn(self)
        
        clkBuilder = ClkBuilder(self, self.clk)
        
        en = self._reg("en", defVal=0)
        first = self._reg("first", defVal=1)
        RxD_data = self._reg("RxD_data", vecT(1 + 8))
        startBitWasNotStartbit = self._sig("startBitWasNotStartbit") 
        # it can happen that there is just glitch on wire and bit was not startbit only begin was resolved wrong 
        # eval because otherwise vhdl int overflows
        sampleTick = clkBuilder.timer(("sampleTick", self.FREQ // self.BAUD // self.OVERSAMPLING), 
                                       enableSig=en,
                                       rstSig=~en)
        
        # synchronize RxD to our clk domain
        RxD_sync = self._reg("RxD_sync", defVal=1)
        RxD_sync ** self.rxd
        
        rxd, rxd_vld = clkBuilder.oversample(RxD_sync,
                                             self.OVERSAMPLING,
                                             sampleTick,
                                             rstSig=~en)

        isLastBit = clkBuilder.timer(("isLastBitTick", 10),
                                     enableSig=rxd_vld,
                                     rstSig=~en)
        
        
        If(en,
           If(rxd_vld, # [TODO] @100M it changes every 352ns it should be 868ns
                RxD_data ** Concat(rxd, RxD_data[9:1]),  # shift data from left
                If(startBitWasNotStartbit,
                    en ** 0,
                    first ** 1,
                ).Else(
                    en ** ~isLastBit,
                    first ** isLastBit,
                )
           )
        ).Elif(RxD_sync._eq(START_BIT),
            # potential start bit detected, begin scanning sequence
            en ** 1,
        )
        startBitWasNotStartbit ** (first & rxd_vld & (rxd != START_BIT))
        self.dataOut.vld ** (isLastBit & RxD_data[0]._eq(START_BIT) & rxd._eq(STOP_BIT))
       
        self.dataOut.data ** RxD_data[9:1]
         

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(UartRx()))
    
         
