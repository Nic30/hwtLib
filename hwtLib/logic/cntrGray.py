#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.interfaces.utils import binToGray, addClkRstn
from hdl_toolkit.synthesizer.codeOps import If
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param


class GrayCntr(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(4)
        
    def _declr(self):
        with self._asExtern():
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
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(GrayCntr))
