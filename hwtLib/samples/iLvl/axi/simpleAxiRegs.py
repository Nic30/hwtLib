#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, connect
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axiLite import AxiLite
from hwtLib.amba.axiLite_comp.conv import AxiLiteConverter


class SimpleAxiRegs(Unit):
    """
    Axi litle mapped registers example,
    0x0 - reg0
    0x4 - reg1
    """
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(32)
        
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.axi = AxiLite()
        
        with self._paramsShared():
            self.conv = AxiLiteConverter([(0, "reg0"),
                                          (4, "reg1")])
        
        
    def _impl(self):
        propagateClkRstn(self)
        connect(self.axi, self.conv.bus, fit=True)
        
        reg0 = self._reg("reg0", vecT(32), defVal=0)
        reg1 = self._reg("reg1", vecT(32), defVal=1)
        
        conv = self.conv
        def connectRegToConveror(convPort, reg):
            If(convPort.dout.vld,
                reg ** convPort.dout.data
            )
            convPort.din ** reg 
        
        connectRegToConveror(conv.reg0, reg0)
        connectRegToConveror(conv.reg1, reg1)

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = SimpleAxiRegs()
    print(toRtl(u))
    
