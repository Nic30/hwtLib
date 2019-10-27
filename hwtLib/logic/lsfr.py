#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.code import Xor, Concat
from hwt.hdl.constants import Time
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.vectorUtils import iterBits
from pyMathBitPrecise.bit_utils import selectBit


class Lsfr(Unit):
    """
    Linear shift feedback register generator,
    form of hardware pseudorandom generator.

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
                                def_val=self.INIT)
        POLY = int(self.POLY)
        xorBits = []
        for i, b in enumerate(iterBits(accumulator)):
            if selectBit(POLY, i):
                xorBits.append(b)
        assert xorBits

        nextBit = Xor(*xorBits)
        accumulator(Concat(accumulator[self.POLY_WIDTH - 1:], nextBit))
        self.dataOut(accumulator[0])


class LsfrTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = Lsfr()
        return cls.u

    def test_simple(self):
        self.runSim(300 * Time.ns)
        self.assertValSequenceEqual(
            self.u.dataOut._ag.data,
            [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0,
             0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1])


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(Lsfr()))
