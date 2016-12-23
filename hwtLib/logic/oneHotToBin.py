#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal, VldSynced
from hwt.interfaces.utils import log2ceil
from hwt.serializer.constants import SERI_MODE
from hwt.synthesizer.codeOps import If, Or, iterBits
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam


class OneHotToBin(Unit):
    """
    Converts one hot signal to binary, bin.vld is high when oneHot != 0
    """
    _serializerMode = SERI_MODE.PARAMS_UNIQ
        
    def _config(self):
        self.ONE_HOT_WIDTH = Param(8)
        
    def _declr(self):
        self.oneHot = Signal(dtype=vecT(self.ONE_HOT_WIDTH)) 
        self.bin = VldSynced()
        self.bin.DATA_WIDTH.set(log2ceil(self.ONE_HOT_WIDTH))
            
    def _impl(self):
        W = evalParam(self.ONE_HOT_WIDTH).val
        
        leadingZeroTop = None  # index is index of first empty record or last one
        for i in reversed(range(W)):
            connections = self.bin.data ** i
            if leadingZeroTop is None:
                leadingZeroTop = connections 
            else:
                leadingZeroTop = If(self.oneHot[i]._eq(1),
                   connections
                ).Else(
                   leadingZeroTop
                )    
        self.bin.vld ** Or(*[bit for bit in iterBits(self.oneHot)])

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = OneHotToBin()
    print(toRtl(u))  



