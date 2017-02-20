#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal, VldSynced
from hwt.serializer.constants import SERI_MODE
from hwt.code import If, Or, iterBits, log2ceil
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


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
        
        self.bin.data ** oneHotToBin(self, self.oneHot)   
        self.bin.vld ** Or(*[bit for bit in iterBits(self.oneHot)])

def oneHotToBin(parent, signals, resName="oneHotToBin"):
    if isinstance(signals, (RtlSignal, Signal)):
        signals = [signals[i] for i in range(signals._dtype.bit_length())]
    else:    
        signals = list(signals)
        
    res = parent._sig(resName, vecT(log2ceil(len(signals))))
    leadingZeroTop = None
    for i, s in enumerate(reversed(signals)):
        connections = res ** (len(signals) - i - 1)
        
        if leadingZeroTop is None:
            leadingZeroTop = connections 
        else:
            leadingZeroTop = If(s,
                                connections
                             ).Else(
                                leadingZeroTop
                             ) 
               
    return res

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = OneHotToBin()
    print(toRtl(u))  



