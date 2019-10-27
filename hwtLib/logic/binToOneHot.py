#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import log2ceil
from hwt.hdl.constants import Time
from hwt.interfaces.std import s, VectSignal
from hwt.serializer.mode import serializeParamsUniq
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param


@serializeParamsUniq
class BinToOneHot(Unit):
    """
    Little endian encoded number to number in one-hot encoding

    .. hwt-schematic::
    """

    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        self.din = VectSignal(log2ceil(self.DATA_WIDTH))
        self.en = s()
        self.dout = VectSignal(self.DATA_WIDTH)._m()

    def _impl(self):
        en = self.en
        dIn = self.din

        WIDTH = self.DATA_WIDTH
        if int(WIDTH) == 1:
            # empty_gen
            self.dout[0](en)
        else:
            for i in range(int(WIDTH)):
                self.dout[i](dIn._eq(i) & en)


class BinToOneHotTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls) -> Unit:
        cls.u = BinToOneHot()
        return cls.u

    def test_basic(self):
        u = self.u
        u.en._ag.data.append(1)
        u.din._ag.data.extend(range(8))

        self.runSim(80 * Time.ns)

        self.assertValSequenceEqual(u.dout._ag.data,
                                    [1 << i for i in range(8)])


if __name__ == "__main__":
    import unittest
    from hwt.synthesizer.utils import toRtl

    print(toRtl(BinToOneHot()))

    suite = unittest.TestSuite()
    # suite.addTest(IndexingTC('test_split'))
    suite.addTest(unittest.makeSuite(BinToOneHotTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
