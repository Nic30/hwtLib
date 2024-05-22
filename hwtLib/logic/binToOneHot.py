#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwt.simulator.simTestCase import SimTestCase
from hwtSimApi.constants import CLK_PERIOD


def binToOneHot(sig, en=1):
    try:
        _en = int(en)
    except:
        _en = None

    res = Concat(*reversed(list(sig._eq(i) for i in range(2 ** sig._dtype.bit_length()))))
    if _en == 1:
        return res
    else:
        return en._ternary(res, res._dtype.from_py(0))


@serializeParamsUniq
class BinToOneHot(HwModule):
    """
    Little endian encoded number to number in one-hot encoding

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(8)

    @override
    def hwDeclr(self):
        self.din = HwIOVectSignal(log2ceil(self.DATA_WIDTH))
        self.en = HwIOSignal()
        self.dout = HwIOVectSignal(self.DATA_WIDTH)._m()

    @override
    def hwImpl(self):
        en = self.en
        dIn = self.din

        WIDTH = self.DATA_WIDTH
        if WIDTH == 1:
            # empty_gen
            self.dout[0](en)
        else:
            self.dout(binToOneHot(dIn, en))


class BinToOneHotTC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        cls.dut = BinToOneHot()
        cls.compileSim(cls.dut)

    def test_basic(self):
        dut = self.dut
        dut.en._ag.data.append(1)
        dut.din._ag.data.extend(range(8))

        self.runSim(8 * CLK_PERIOD)

        self.assertValSequenceEqual(dut.dout._ag.data,
                                    [1 << i for i in range(8)])


if __name__ == "__main__":
    import unittest
    from hwt.synth import to_rtl_str

    print(to_rtl_str(BinToOneHot()))

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([BinToOneHotTC("test_split")])
    suite = testLoader.loadTestsFromTestCase(BinToOneHotTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
