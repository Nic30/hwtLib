#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.code import Xor, Concat
from hwt.constants import Time
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule
from hwt.synthesizer.vectorUtils import iterBits
from pyMathBitPrecise.bit_utils import get_bit


class Lfsr(HwModule):
    """
    Linear shift feedback register generator,
    form of hardware pseudorandom generator.

    .. hwt-autodoc::
    """

    def _config(self):
        self.POLY_WIDTH = HwParam(8)
        self.POLY = HwParam(0x88)
        self.INIT = HwParam(1)

    def _declr(self):
        addClkRstn(self)
        self.dataOut = HwIOSignal()._m()

    def _impl(self):
        accumulator = self._reg("accumulator",
                                HBits(self.POLY_WIDTH),
                                def_val=self.INIT)
        POLY = int(self.POLY)
        xorBits = []
        for i, b in enumerate(iterBits(accumulator)):
            if get_bit(POLY, i):
                xorBits.append(b)
        assert xorBits

        nextBit = Xor(*xorBits)
        accumulator(Concat(accumulator[self.POLY_WIDTH - 1:], nextBit))
        self.dataOut(accumulator[0])


class LfsrTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = Lfsr()
        cls.compileSim(cls.dut)

    def test_simple(self):
        self.runSim(300 * Time.ns)
        self.assertValSequenceEqual(
            self.dut.dataOut._ag.data,
            [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0,
             0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1])


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(Lfsr()))
