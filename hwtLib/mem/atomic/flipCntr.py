#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal, HandshakeSync, \
    RegCntrl
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.serializer.constants import SERI_MODE
from hwt.code import If
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.mem.atomic.flipReg import FlipRegister


class FlipCntr(Unit):
    """
    Counter with FlipRegister which is form memory with atomic access
    
    interface doFilip drives switching of memories in flip register
    dataIn has higher priority than doIncr
    """
    _serializerMode = SERI_MODE.ONCE
    
    def _config(self):
        self.DATA_WIDTH = Param(18)

    def _declr(self):
        with self._paramsShared():
            addClkRstn(self)
            self.doIncr = Signal()
            self.doFlip = HandshakeSync()
            self.data = RegCntrl()
            self.cntr = FlipRegister()
    
    def flipHandler(self):
        self.doFlip.rd ** 1
        
        flipSt = self._reg("flipState", defVal=0)
        If(self.doFlip.vld,
            flipSt ** ~flipSt
        )
        self.cntr.select_sig ** flipSt
        
    
    def dataHanldler(self):
        cntr = self.cntr
        cntr.first.dout.data ** (cntr.first.din + 1)
        cntr.first.dout.vld ** self.doIncr
        
        cntr.second ** self.data
        
    
    def _impl(self):
        propagateClkRstn(self)
        self.flipHandler()
        self.dataHanldler()
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(FlipCntr()))
