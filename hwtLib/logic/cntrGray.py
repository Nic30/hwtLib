#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, binToGray
from hwt.hdl.constants import Time
from hwt.interfaces.std import Signal, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.simulator.simTestCase import SimTestCase, SingleUnitSimTestCase
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


@serializeParamsUniq
class GrayCntr(Unit):
    """
    Counter for gray code

    .. hwt-schematic::
    """

    def _config(self):
        self.DATA_WIDTH = Param(4)
        self.INIT_VAL = Param(0)  # binary

    def _declr(self):
        addClkRstn(self)
        self.en = Signal()

        self.dataOut = VectSignal(self.DATA_WIDTH)._m()

    def _impl(self):
        binCntr = self._reg("cntr_bin_reg", self.dataOut._dtype, self.INIT_VAL)

        self.dataOut(binToGray(binCntr))

        If(self.en,
           binCntr(binCntr + 1)
        )


class GrayCntrTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls) -> Unit:
        cls.u = GrayCntr()
        return cls.u

    def test_count(self):
        u = self.u
        u.en._ag.data.append(1)

        self.runSim(170 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data,
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
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(GrayCntrTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

    from hwt.synthesizer.utils import toRtl
    print(toRtl(GrayCntr()))
