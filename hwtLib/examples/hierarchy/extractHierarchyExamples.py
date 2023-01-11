#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.examples.hierarchy.extractHierarchy import extractRegsToSubunit


class UnitWidthDynamicallyGeneratedSubunitsForRegisters(Unit):

    def _declr(self) -> None:
        addClkRstn(self)
        self.i = VectSignal(8)
        self.o = VectSignal(8)._m()

    def _impl(self) -> None:
        r = [self._reg(f"r{i:d}", Bits(8), def_val=0) for i in range(2)]
        r[0](self.i)
        r[1](r[0])
        self.o(r[1])
        
        self.uForR0 = extractRegsToSubunit([r[0], ])
        self.uForR1 = extractRegsToSubunit([r[1], ])


class UnitWidthDynamicallyGeneratedSubunitsForRegistersWithExpr(Unit):

    def _declr(self) -> None:
        addClkRstn(self)
        self.i = VectSignal(8)
        self.o = VectSignal(8)._m()

    def _impl(self) -> None:
        r = [self._reg(f"r{i:d}", Bits(8), def_val=0) for i in range(2)]
        r[0](self.i + 1)
        r[1]((r[0] ^ 1) + 1 + r[0])
        self.o(r[1])
        
        self.uForR0 = extractRegsToSubunit([r[0], ])
        self.uForR1 = extractRegsToSubunit([r[1], ])


class UnitWidthDynamicallyGeneratedSubunitsForManyRegisters(Unit):

    def _declr(self) -> None:
        addClkRstn(self)
        self.i0 = VectSignal(8)
        self.i1 = VectSignal(8)
        
        self.o = VectSignal(8)._m()

    def _impl(self) -> None:
        r = [[self._reg(f"r{stI}_{i:d}", Bits(8), def_val=0)
              for i in range(2)]
              for stI in range(2)]
        r[0][0](self.i0)
        r[0][1](self.i1)
        
        r[1][0](r[0][0])
        r[1][1](r[0][1])
        self.o(r[1][0] + r[1][1])
        
        self.uForR0 = extractRegsToSubunit(r[0])
        self.uForR1 = extractRegsToSubunit(r[1])


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    print(to_rtl_str(UnitWidthDynamicallyGeneratedSubunitsForManyRegisters()))
