#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.array import Array
from hwt.interfaces.std import Signal, Clk
from hwt.code import If
from hwt.synthesizer.interfaceLevel.unit import Unit


class SimpleRom(Unit):
    def _declr(self):
        self.addr = Signal(dtype=vecT(2))
        self.dout = Signal(dtype=vecT(8))
        
    def _impl(self):
        rom = self._sig("rom_data", Array(vecT(8), 4), defVal=[1, 2, 3, 4])
        self.dout ** rom[self.addr]

class SimpleSyncRom(SimpleRom):
    def _declr(self):
        super()._declr()
        self.clk = Clk()
    
    def _impl(self):
        rom = self._sig("rom_data", Array(vecT(8), 4), defVal=[1, 2, 3, 4])
        
        If(self.clk._onRisingEdge(),
           self.dout ** rom[self.addr]  
        )


if __name__ == "__main__":  # alias python main function
    from hwt.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SimpleSyncRom))
