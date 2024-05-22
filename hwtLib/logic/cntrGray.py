#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.constants import Time
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.mainBases import RtlSignalBase
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwt.simulator.simTestCase import SimTestCase


def binToGray(sigOrConst) -> RtlSignalBase:
    """
    Convert value or signal from binary encoding to gray encoding
    """
    return (sigOrConst >> 1) ^ sigOrConst
    #width = sigOrConst._dtype.bit_length()
    #return Concat(sigOrConst[width - 1],
    #              sigOrConst[width - 1:0] ^ sigOrConst[width:1])


@serializeParamsUniq
class GrayCntr(HwModule):
    """
    Counter for gray code

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(4)
        self.INIT_VAL = HwParam(0)  # binary

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.en = HwIOSignal()

        self.dataOut = HwIOVectSignal(self.DATA_WIDTH)._m()

    @override
    def hwImpl(self):
        binCntr = self._reg("cntr_bin_reg", self.dataOut._dtype, self.INIT_VAL)

        self.dataOut(binToGray(binCntr))

        If(self.en,
           binCntr(binCntr + 1)
        )


class GrayCntrTC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls) -> HwModule:
        cls.dut = GrayCntr()
        cls.compileSim(cls.dut)

    def test_count(self):
        dut = self.dut
        dut.en._ag.data.append(1)

        self.runSim(170 * Time.ns)
        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    [
                                        0b0000,
                                        0b0001,
                                        0b0011,
                                        0b0010,
                                        0b0110,
                                        0b0111,
                                        0b0101,
                                        0b0100,
                                        0b1100,
                                        0b1101,
                                        0b1111,
                                        0b1110,
                                        0b1010,
                                        0b1011,
                                        0b1001,
                                        0b1000,
                                    ])


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(GrayCntrTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    from hwt.synth import to_rtl_str
    print(to_rtl_str(GrayCntr()))
