#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal, VldSynced
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.code import FsmBuilder, If, Concat, log2ceil
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.uart.baudGen import UartBaudGen


IDLE = 0b0000
SYNC = 0b0001
BIT0 = 0b1000 
BIT1 = 0b1001 
BIT2 = 0b1010 
BIT3 = 0b1011 
BIT4 = 0b1100 
BIT5 = 0b1101 
BIT6 = 0b1110 
BIT7 = 0b1111 
STOP = 0b0010 

class UartRx(Unit):
    def _config(self):
        self.FREQ = Param(int(100e6))
        self.BAUD = Param(115200)
        # needs to be a power of 2
        # we oversample the line at a fixed rate to capture each RxD data bit at the "right" time
        # 8 times oversampling by default, use 16 for higher quality reception
        self.OVERSAMPLING = Param(8)
        
    def _declr(self):
        os = evalParam(self.OVERSAMPLING).val
        baud = evalParam(self.BAUD).val
        freq = evalParam(self.FREQ).val
        
        addClkRstn(self)
        self.dataOut = VldSynced()
        self.dataOut.DATA_WIDTH.set(8)
        self.idle = Signal()

        self.rxd = Signal()
            
            
        with self._paramsShared():
            self.baudGen = UartBaudGen()
            
        assert freq > baud * os, "Frequency too low for current Baud rate and oversampling"
        assert os >= 8 and (os & (os - 1)) == 0, "Invalid oversampling value"
    
    def _impl(self):
        propagateClkRstn(self)
        sampleNow = self._sig("sampleNow")
        
        self.baudGen.enable ** 1
        
        osTick = self.baudGen.tick
        # synchronize RxD to our clk domain
        RxD_sync = self._reg("RxD_sync", vecT(2), 0b11)
        If(osTick,
          RxD_sync ** Concat(RxD_sync[0], self.rxd)
        )
        
        # and filter it
        Filter_cnt = self._reg("Filter_cnt", vecT(2), 0b11) 
        RxD_bit = self._reg("RxD_bit", defVal=1)

        If(osTick,
            If(RxD_sync[1] & (Filter_cnt != 0b11),
              Filter_cnt ** (Filter_cnt + 1)
            ).Elif(~RxD_sync[1] & (Filter_cnt != 0),
              Filter_cnt ** (Filter_cnt - 1)
            ),
            If(Filter_cnt._eq(0b11),
              RxD_bit ** 1
            ).Elif(Filter_cnt._eq(0),
              RxD_bit ** 0
            )
        )
        
        RxD_state = FsmBuilder(self, vecT(4))\
        .Trans(IDLE,
            (~RxD_bit, SYNC)
        ).Trans(SYNC,
            (sampleNow, BIT0)
        ).Trans(BIT0,
            (sampleNow, BIT1)
        ).Trans(BIT1,
            (sampleNow, BIT2)
        ).Trans(BIT2,
            (sampleNow, BIT3)
        ).Trans(BIT3,
            (sampleNow, BIT4)
        ).Trans(BIT4,
            (sampleNow, BIT5)
        ).Trans(BIT5,
            (sampleNow, BIT6)
        ).Trans(BIT6,
            (sampleNow, BIT7)
        ).Trans(BIT7,
            (sampleNow, STOP)
        ).Trans(STOP,
            (sampleNow, IDLE)
        ).Default(
            IDLE
        ).stateReg

        
        # and decide when is the good time to sample the RxD line
        l2o = log2ceil(self.OVERSAMPLING)
        OversamplingCnt = self._reg("OversamplingCnt", vecT(l2o - 2, False), 0)
        If(osTick,
            If(RxD_state._eq(0),
              OversamplingCnt ** 0
            ).Else(
              OversamplingCnt ** (OversamplingCnt + 1)    
            )
        )
        sampleNow ** (osTick & OversamplingCnt._eq(self.OVERSAMPLING // 2 - 1))
        
        # data collecting
        RxD_data = self._reg("RxD_data", vecT(8), 0)
        If(sampleNow & RxD_state[3],
           RxD_data ** Concat(RxD_bit, RxD_data[:1]) 
        )
        self.dataOut.data ** RxD_data
        
        
        RxD_data_ready = self._reg("RxD_data_ready", defVal=0)
        # make sure a stop bit is received
        RxD_data_ready ** (sampleNow & RxD_state._eq(STOP) & RxD_bit)
        self.dataOut.vld ** RxD_data_ready
        
        GapCnt = self._reg("GapCnt", vecT(l2o + 2), 0)
        If(RxD_state != IDLE,
           GapCnt ** 0
        ).Elif(osTick & ~GapCnt[log2ceil(self.OVERSAMPLING + 1)],
           GapCnt ** (GapCnt + 1)  
        )
        
        self.idle ** GapCnt[l2o + 1]

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(UartRx()))
    
         
