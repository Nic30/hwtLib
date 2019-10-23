#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.amba.axis_comp.en import AxiS_en
from pyMathBitPrecise.bit_utils import mask


class AxiS_en_TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = AxiS_en()
        u.USE_STRB = True
        return u

    def test_break(self):
        m = mask(64 // 8)
        MAGIC = 987
        u = self.u
        u.en._ag.data += [0]
        u.dataIn._ag.data.append((MAGIC, m, 1))
        self.runSim(100 * Time.ns)
        self.assertEmpty(u.dataOut._ag.data)

    def test_pass(self):
        m = mask(64 // 8)
        MAGIC = 987
        u = self.u
        u.en._ag.data += [1]
        d = [(MAGIC + 1, m, 1),
             (MAGIC + 2, m, 0),
             (MAGIC + 3, m, 1),
             (MAGIC + 4, m, 0),
             (MAGIC + 5, m, 0),
             (MAGIC + 6, m, 1)
             ]
        u.dataIn._ag.data.extend(d)
        self.runSim(100 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data, d)

    def test_passFirstBreakContinue(self):
        m = mask(64 // 8)
        MAGIC = 987
        u = self.u
        u.en._ag.data += [1, 0, 0, 0, 1]
        d = [(MAGIC + 1, m, 1),
             (MAGIC + 2, m, 0),
             (MAGIC + 3, m, 1),
             (MAGIC + 4, m, 0),
             (MAGIC + 5, m, 0),
             (MAGIC + 6, m, 1)
             ]
        u.dataIn._ag.data.extend(d)
        self.runSim(100 * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data, d)

    def test_randomized(self):
        self.randomize(self.u.dataIn)
        self.randomize(self.u.dataOut)

        m = mask(64 // 8)
        MAGIC = 987
        u = self.u

        d = [(MAGIC + 1, m, 1),
             (MAGIC + 2, m, 0),
             (MAGIC + 3, m, 1),
             (MAGIC + 4, m, 0),
             (MAGIC + 5, m, 0),
             (MAGIC + 6, m, 1)
             ]
        u.en._ag.data.extend([(i + 1) % 2 for i in range(20 * len(d))])
        u.dataIn._ag.data.extend(d)
        self.runSim(200 * len(d) * Time.ns)
        self.assertValSequenceEqual(u.dataOut._ag.data, d)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(StructWriter_TC('test_doubleField'))
    suite.addTest(unittest.makeSuite(AxiS_en_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
