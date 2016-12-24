#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal, BramPort_withoutClk, Clk
from hwt.interfaces.utils import propagateClk
from hwt.serializer.constants import SERI_MODE
from hwt.code import If
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import evalParam
from hwtLib.mem.ram import RamSingleClock


class FlipRam(Unit):
    """
    Switchable RAM, there are two memories and two sets of ports,
    Each set of ports is every time connected to opposite ram.
    By select you can choose between RAMs.
    
    This component is meant to be form of synchronization.
    Example first RAM is connected to first set of ports, writer performs actualizations on first RAM
    and reader reads data from second ram by second set of ports.
    
    Then select is set and access is flipped. Reader now has access to RAM 0 and writer to RAM 1.
    """
    _serializerMode = SERI_MODE.PARAMS_UNIQ
    
    def _config(self):
        RamSingleClock._config(self)

    def _declr(self):
        PORT_CNT = evalParam(self.PORT_CNT).val
        
        with self._paramsShared():
            self.clk = Clk()
            self.firstA = BramPort_withoutClk()
            self.secondA = BramPort_withoutClk()
            
            if PORT_CNT == 2:
                self.firstB = BramPort_withoutClk()
                self.secondB = BramPort_withoutClk()
            elif PORT_CNT > 2:
                raise NotImplementedError()
            
            self.select_sig = Signal()  
            
                
            self.ram0 = RamSingleClock()
            self.ram1 = RamSingleClock()

    def _impl(self):
        propagateClk(self)
        PORT_CNT = evalParam(self.PORT_CNT).val
        
        fa = self.firstA
        sa = self.secondA
        
        If(self.select_sig,
           self.ram0.a ** fa,
           self.ram1.a ** sa
        ).Else(
           self.ram0.a ** sa,
           self.ram1.a ** fa 
        )
        if PORT_CNT == 2:
            fb = self.firstB
            sb = self.secondB
            If(self.select_sig,
               self.ram0.b ** fb,
               self.ram1.b ** sb,
            ).Else(
               self.ram0.b ** sb,
               self.ram1.b ** fb
            )
          
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(FlipRam))
