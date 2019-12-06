#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.examples.builders.hsBuilderSplit import HsBuilderSplit
from pycocotb.constants import CLK_PERIOD


class HsBuilderSplit_TC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        return HsBuilderSplit()

    def test_all(self):
        u = self.u
        MAGIC = 11

        aRef = [MAGIC + i for i in range(6)]
        u.a._ag.data.extend(aRef)

        bRef = [MAGIC + i + 6 for i in range(6)]
        u.b._ag.data.extend(bRef)

        cRef = [MAGIC + i + 12 for i in range(6)]
        u.c._ag.data.extend(cRef)

        dRef = [MAGIC + i + 18 for i in range(6)]
        u.d._ag.data.extend(dRef)

        eRef = [MAGIC + i + 24 for i in range(6)]
        u.e._ag.data.extend(eRef)
        eSel = [0, 2, 1, 2, 1, 0]
        u.e_select._ag.data.extend([1 << i for i in eSel])

        self.runSim(30 * CLK_PERIOD)

        eq = self.assertValSequenceEqual
        for a in [u.a_0, u.a_1, u.a_2]:
            eq(a._ag.data, aRef)

        eq(u.b_0._ag.data, [MAGIC + 6, MAGIC + 9])
        eq(u.b_1._ag.data, [MAGIC + 7, MAGIC + 10])
        eq(u.b_2._ag.data, [MAGIC + 8, MAGIC + 11])
        eq(u.b_selected._ag.data, [1 << (i % 3) for i in range(6)])
        eq(u.c_0._ag.data, cRef)
        eq(u.c_1._ag.data, [])

        # [1, 2, 1, 0, 1, 2]
        eq(u.d_0._ag.data, [dRef[3], ])
        eq(u.d_1._ag.data, [dRef[0], dRef[2], dRef[4]])
        eq(u.d_2._ag.data, [dRef[1], dRef[5]])

        eq(u.e_0._ag.data, [eRef[0], eRef[5]])
        eq(u.e_1._ag.data, [eRef[2], eRef[4]])
        eq(u.e_2._ag.data, [eRef[1], eRef[3]])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HsBuilderSplit_TC('test_reply1x'))
    suite.addTest(unittest.makeSuite(HsBuilderSplit_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
