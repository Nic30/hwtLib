#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwtLib.examples.hierarchy.extractHierarchy import extractRegsToSubmodule


class HwModuleWidthDynamicallyGeneratedSubunitsForRegisters(HwModule):

    def hwDeclr(self) -> None:
        addClkRstn(self)
        self.i = HwIOVectSignal(8)
        self.o = HwIOVectSignal(8)._m()

    def hwImpl(self) -> None:
        r = [self._reg(f"r{i:d}", HBits(8), def_val=0) for i in range(2)]
        r[0](self.i)
        r[1](r[0])
        self.o(r[1])
        
        self.uForR0 = extractRegsToSubmodule([r[0], ])
        self.uForR1 = extractRegsToSubmodule([r[1], ])


class HwModuleWidthDynamicallyGeneratedSubunitsForRegistersWithExpr(HwModule):

    def hwDeclr(self) -> None:
        addClkRstn(self)
        self.i = HwIOVectSignal(8)
        self.o = HwIOVectSignal(8)._m()

    def hwImpl(self) -> None:
        r = [self._reg(f"r{i:d}", HBits(8), def_val=0) for i in range(2)]
        r[0](self.i + 1)
        r[1]((r[0] ^ 1) + 1 + r[0])
        self.o(r[1])
        
        self.uForR0 = extractRegsToSubmodule([r[0], ])
        self.uForR1 = extractRegsToSubmodule([r[1], ])


class HwModuleWidthDynamicallyGeneratedSubunitsForManyRegisters(HwModule):

    def hwDeclr(self) -> None:
        addClkRstn(self)
        self.i0 = HwIOVectSignal(8)
        self.i1 = HwIOVectSignal(8)
        
        self.o = HwIOVectSignal(8)._m()

    def hwImpl(self) -> None:
        r = [[self._reg(f"r{stI}_{i:d}", HBits(8), def_val=0)
              for i in range(2)]
              for stI in range(2)]
        r[0][0](self.i0)
        r[0][1](self.i1)
        
        r[1][0](r[0][0])
        r[1][1](r[0][1])
        self.o(r[1][0] + r[1][1])
        
        self.uForR0 = extractRegsToSubmodule(r[0])
        self.uForR1 = extractRegsToSubmodule(r[1])


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(HwModuleWidthDynamicallyGeneratedSubunitsForManyRegisters()))
