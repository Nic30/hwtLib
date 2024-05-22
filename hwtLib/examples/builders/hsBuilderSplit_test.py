#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.builders.hsBuilderSplit import HsBuilderSplit
from hwtSimApi.constants import CLK_PERIOD


class HsBuilderSplit_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        cls.dut = HsBuilderSplit()
        cls.compileSim(cls.dut)

    def test_all(self):
        dut = self.dut
        MAGIC = 11

        aRef = [MAGIC + i for i in range(6)]
        dut.a._ag.data.extend(aRef)

        bRef = [MAGIC + i + 6 for i in range(6)]
        dut.b._ag.data.extend(bRef)

        cRef = [MAGIC + i + 12 for i in range(6)]
        dut.c._ag.data.extend(cRef)

        dRef = [MAGIC + i + 18 for i in range(6)]
        dut.d._ag.data.extend(dRef)

        eRef = [MAGIC + i + 24 for i in range(6)]
        dut.e._ag.data.extend(eRef)
        eSel = [0, 2, 1, 2, 1, 0]
        dut.e_select._ag.data.extend([1 << i for i in eSel])

        self.runSim(30 * CLK_PERIOD)

        eq = self.assertValSequenceEqual
        for a in [dut.a_0, dut.a_1, dut.a_2]:
            eq(a._ag.data, aRef)

        eq(dut.b_0._ag.data, [MAGIC + 6, MAGIC + 9])
        eq(dut.b_1._ag.data, [MAGIC + 7, MAGIC + 10])
        eq(dut.b_2._ag.data, [MAGIC + 8, MAGIC + 11])
        eq(dut.b_selected._ag.data, [1 << (i % 3) for i in range(6)])
        eq(dut.c_0._ag.data, cRef)
        eq(dut.c_1._ag.data, [])

        # [1, 2, 1, 0, 1, 2]
        eq(dut.d_0._ag.data, [dRef[3], ])
        eq(dut.d_1._ag.data, [dRef[0], dRef[2], dRef[4]])
        eq(dut.d_2._ag.data, [dRef[1], dRef[5]])

        eq(dut.e_0._ag.data, [eRef[0], eRef[5]])
        eq(dut.e_1._ag.data, [eRef[2], eRef[4]])
        eq(dut.e_2._ag.data, [eRef[1], eRef[3]])


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HsBuilderSplit_TC("test_reply1x")])
    suite = testLoader.loadTestsFromTestCase(HsBuilderSplit_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
