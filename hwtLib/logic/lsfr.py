#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.bitmask import selectBit
from hwt.code import Xor, Concat
from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.vectorUtils import iterBits


class Lsfr(Unit):
    """
    Linear shift feedback register,
    form of hardware pseudorandom generator
    """
    def _config(self):
        self.POLY_WIDTH = Param(8)
        self.POLY = Param(0x88)
        self.SEED = Param(1)

    def _declr(self):
        addClkRstn(self)
        self.dataOut = Signal()

    def _impl(self):
        accumulator = self._reg("accumulator",
                                vecT(self.POLY_WIDTH),
                                defVal=self.SEED)
        POLY = int(self.POLY)
        xorBits = []
        for i, b in enumerate(iterBits(accumulator)):
            if selectBit(POLY, i):
                xorBits.append(b)
        assert xorBits

        nextBit = Xor(*xorBits)
        accumulator ** Concat(accumulator[self.POLY_WIDTH - 1:], nextBit)
        self.dataOut ** accumulator[0]


class LsfrTC(SimTestCase):
    def test_simple(self):
        u = Lsfr()
        self.prepareUnit(u)

        self.doSim(300 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data,
         [1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0,
          0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1])


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(Lsfr()))
