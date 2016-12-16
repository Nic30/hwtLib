#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit


class ConstDriverUnit(Unit):
    def _declr(self):
        self.out0 = Signal()
        self.out1 = Signal()
    
    def _impl(self):
        self.out0 ** 0
        self.out1 ** 1 


if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(ConstDriverUnit()))