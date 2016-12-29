#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.enum import Enum
from hwt.interfaces.std import ReqDoneSync, Signal
from hwt.interfaces.utils import addClkRstn
from hwt.code import FsmBuilder, If, log2ceil
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam


class DelayMs(Unit):
    
    def _config(self):
        self.FREQ = Param(int(100e6))  # [hz]
        self.MAX_DELAY = Param(100)  # [ms]
    
    def _declr(self):
        addClkRstn(self)
        self.delayTime = Signal(dtype=vecT(log2ceil(self.MAX_DELAY)))
        self.acivate = ReqDoneSync()
            
    def _impl(self):
        
        stT = Enum("stT", ["idle", 'hold', 'done'])
        clksPerMs = evalParam(self.FREQ) // 1000
        
        cntrClk = self._reg("cntrClk", vecT(log2ceil(clksPerMs)))
        cntrMs = self._reg("cntrMs", self.delayTime._dtype) 
        
        stFsm = FsmBuilder(self, stT)
        st = stFsm.stateReg
        act = self.acivate
        
        
        act.done ** (act.req & st._eq(stT.done))
        
        stFsm\
        .Trans(stT.idle,
            (act.req, stT.hold)
        ).Trans(stT.hold,
            (cntrMs._eq(self.delayTime), stT.done)
        ).Default(# stT.done,
            (~act.req, stT.idle)
        )
        
        
        # Creates ms_counter that counts at 1KHz
        If(st._eq(stT.hold),
            If(cntrClk._eq(clksPerMs),
                cntrClk ** 0,
                cntrMs ** (cntrMs + 1)
            ).Else(
                cntrClk ** (cntrClk + 1),
            )
        ).Else(
            cntrClk ** 0,
            cntrMs ** 0  
        )
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    u = DelayMs()
    print(toRtl(u))
