#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Handshaked, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.code import FsmBuilder, If, sll
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.uart.baudGen import UartBaudGen


IDLE = 0
START = 0b0100
BIT0 = 0b1000 
BIT1 = 0b1001 
BIT2 = 0b1010 
BIT3 = 0b1011 
BIT4 = 0b1100 
BIT5 = 0b1101 
BIT6 = 0b1110 
BIT7 = 0b1111 
STOP1 = 0b0001 
STOP2 = 0b0010 

class UartTx(Unit):
    def _config(self):
        self.FREQ = Param(int(100e6))
        self.BAUD = Param(115200)
    
    def _declr(self):
        addClkRstn(self)
        self.dataIn = Handshaked()
        self.dataIn.DATA_WIDTH.set(8)
        self.txd = Signal()
        
        with self._paramsShared():
            self.baudGen = UartBaudGen()
    
    def _impl(self):
        propagateClkRstn(self)
        tick = self.baudGen.tick
        
        st = FsmBuilder(self, vecT(4))\
        .Trans(IDLE,
            (self.dataIn.vld, START)
        ).Trans(START,
            (tick, BIT0)
        ).Trans(BIT0,
            (tick, BIT1)
        ).Trans(BIT1,
            (tick, BIT2)
        ).Trans(BIT2,
            (tick, BIT3)
        ).Trans(BIT3,
            (tick, BIT4)
        ).Trans(BIT4,
            (tick, BIT5)
        ).Trans(BIT5,
            (tick, BIT6)
        ).Trans(BIT6,
            (tick, BIT7)
        ).Trans(BIT7,
            (tick, STOP1)
        ).Trans(STOP1,
            (tick, STOP2)
        ).Trans(STOP2,
            (tick, IDLE)
        ).stateReg
        bussy = st != IDLE
        self.baudGen.enable ** bussy
        

        self.dataIn.rd ** ~bussy
        
        TxD_shift = self._reg("TxD_shift", vecT(8))
        
        If(~bussy & self.dataIn.vld,
            TxD_shift ** self.dataIn.data
        ).Elif(st[3] & tick,
            TxD_shift ** sll(TxD_shift, 1)
        )
        
        self.txd ** ((st < 4) | (st[3] & TxD_shift[0]))
 
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = UartTx()
    print(toRtl(u)) 
        
