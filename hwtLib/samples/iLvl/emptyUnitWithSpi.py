#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.intfLvl import EmptyUnit 
from hdl_toolkit.synthesizer.shortcuts import toRtl
from hwtLib.interfaces.peripheral import Spi


class EmptyUnitWithSpi(EmptyUnit):
    def _declr(self):
        with self._asExtern():
            self.spi = Spi()
    
    
if __name__ == "__main__":
    print(toRtl(EmptyUnitWithSpi()))
