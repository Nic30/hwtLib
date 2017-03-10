#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Switch, sll
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.enum import Enum
from hwt.interfaces.std import Handshaked, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.uart.baudGen import UartBaudGen


# https://github.com/pabennett/uart/blob/master/source/uart.vhd
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
            self.baudGen.OVERSAMPLING.set(1)
    
    def _impl(self):
        propagateClkRstn(self)
        tick = self.baudGen.bitTick
        din = self.dataIn
        
        r = self._reg
        
        txData = r("txData", defVal=0)
        cntr = r("cntr", vecT(3, False), 0)
        data = r("data", vecT(8))
        
        stT = Enum("txSt_t", ["startBit", "sendData", "stopBit"])
        st = r("st", stT, defVal=stT.startBit)
        
        Switch(st)\
        .Case(stT.startBit,
            If(tick & din.vld,
               txData ** 0,
               st ** stT.sendData,
               cntr ** 0,
               data ** din.data
            ),
            din.rd ** tick
        ).Case(stT.sendData,
            If(tick,
               txData ** data[0],
               data ** sll(data, 1),
               If(cntr._eq(8 - 1),
                  st ** stT.stopBit
               ).Else(
                  cntr ** (cntr + 1)
               )
            )
        ).Case(stT.stopBit,
            If(tick,
               txData ** 1,
               st ** stT.startBit
            )
        )
        
        self.txd ** txData
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = UartTx()
    print(toRtl(u)) 
        
