#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.constants import Time, NOP, WRITE, READ
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.mem.atomic.flipRam import FlipRam


class FlipRamTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = FlipRam()
        return cls.u

    def test_basic(self):
        u = self.u
        MAGIC0 = 80
        MAGIC1 = 30
        N = 10

        u.select_sig._ag.data.append(0)
        u.firstA._ag.requests.extend([(WRITE, i, MAGIC0 + i)
                                      for i in range(N)])
        u.secondA._ag.requests.extend([(WRITE, i, MAGIC1 + i)
                                       for i in range(N)])

        u.firstA._ag.requests.extend([(READ, i) for i in range(N)])
        u.secondA._ag.requests.extend([(READ, i) for i in range(N)])

        self.runSim(N * 40 * Time.ns)

        self.assertValSequenceEqual(u.firstA._ag.readed, [MAGIC0 + i
                                                          for i in range(N)])
        self.assertValSequenceEqual(u.secondA._ag.readed, [MAGIC1 + i
                                                           for i in range(N)])

    def test_flip(self):
        u = self.u
        MAGIC0 = 80
        MAGIC1 = 30
        N = 3

        u.select_sig._ag.data.extend(
            [0 for _ in range(N)]
            + [1 for _ in range(2 * N)])
        u.firstA._ag.requests.extend(
            [(WRITE, i, MAGIC0 + i) for i in range(N)]
            + [NOP for _ in range(2 * N)])
        u.secondA._ag.requests.extend(
            [(WRITE, i, MAGIC1 + i) for i in range(N)]
            + [NOP for _ in range(2 * N)])

        u.firstA._ag.requests.extend([(READ, i % N) for i in range(N)])
        u.secondA._ag.requests.extend([(READ, i % N) for i in range(N)])

        self.runSim(3 * N * 40 * Time.ns)

        self.assertValSequenceEqual(u.firstA._ag.readed, [MAGIC1 + i
                                                          for i in range(N)])
        self.assertValSequenceEqual(u.secondA._ag.readed, [MAGIC0 + i
                                                           for i in range(N)])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_withStops'))
    suite.addTest(unittest.makeSuite(FlipRamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
