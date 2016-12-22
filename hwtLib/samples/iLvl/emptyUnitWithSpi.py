#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.intfLvl import EmptyUnit 
from hwt.synthesizer.shortcuts import toRtl
from hwtLib.interfaces.peripheral import Spi


class EmptyUnitWithSpi(EmptyUnit):
    def _declr(self):
        self.spi = Spi()
    
    
if __name__ == "__main__":
    print(toRtl(EmptyUnitWithSpi()))
