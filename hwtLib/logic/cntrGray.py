#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.code import If, binToGray
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param


class GrayCntr(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(4)
        
    def _declr(self):
        addClkRstn(self)
        self.en = Signal()

        self.dataOut = Signal(dtype=vecT(self.DATA_WIDTH))
            
    def _impl(self):
        binCntr = self._reg("cntr_bin_reg", self.dataOut._dtype, 1) 
        
        If(self.rst_n._isOn(),
           self.dataOut ** 0
        ).Else(
           self.dataOut ** binToGray(binCntr)
        )
        
        If(self.en,
           binCntr ** (binCntr + 1)
        )

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(GrayCntr))
