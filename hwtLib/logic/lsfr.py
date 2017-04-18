#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.bitmask import selectBit
from hwt.code import iterBits, Xor, Concat
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.logic.crcPoly import CRC_32


class Lsfr(Unit):
    """
    Linear shift feedback register,
    form of hardware pseudorandom generator
    """
    def _config(self):
        self.POLY_WIDTH = Param(32)
        self.POLY = Param(CRC_32)
        self.SEED = Param(383)

    def _declr(self):
        addClkRstn(self)
        self.dataOut = Signal()

    def _impl(self):
        accumulator = self._reg("accumulator",
                                vecT(self.POLY_WIDTH),
                                defVal=self.SEED)
        POLY = evalParam(self.POLY).val
        xorBits = []
        for i, b in enumerate(iterBits(accumulator)):
            if selectBit(POLY, i):
                xorBits.append(b)
        assert xorBits

        nextBit = Xor(*xorBits)
        accumulator ** Concat(accumulator[self.POLY_WIDTH-1:], nextBit)
        self.dataOut ** accumulator[0]

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(Lsfr()))
