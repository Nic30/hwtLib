#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.bitmask import selectBit
from hwt.code import Xor, Concat
from hwt.hdl.constants import Time
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.vectorUtils import iterBits


class Lsfr(Unit):
    """
    Linear shift feedback register,
    form of hardware pseudorandom generator

    .. hwt-schematic::
    """

    def _config(self):
        self.POLY_WIDTH = Param(8)
        self.POLY = Param(0x88)
        self.INIT = Param(1)

    def _declr(self):
        addClkRstn(self)
        self.dataOut = Signal()._m()

    def _impl(self):
        accumulator = self._reg("accumulator",
                                Bits(self.POLY_WIDTH),
                                defVal=self.INIT)
        POLY = int(self.POLY)
        xorBits = []
        for i, b in enumerate(iterBits(accumulator)):
            if selectBit(POLY, i):
                xorBits.append(b)
        assert xorBits

        nextBit = Xor(*xorBits)
        accumulator(Concat(accumulator[self.POLY_WIDTH - 1:], nextBit))
        self.dataOut(accumulator[0])


class LsfrTC(SimTestCase):
    def test_simple(self):
        u = Lsfr()
        self.prepareUnit(u)

        self.runSim(300 * Time.ns)
        self.assertValSequenceEqual(
            u.dataOut._ag.data,
            [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0,
             0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1])


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(Lsfr()))
