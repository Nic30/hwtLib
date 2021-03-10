#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwtSimApi.constants import CLK_PERIOD
from hwtLib.amba.axi_comp.cache.ramTransactional import RamTransactional
from hwt.hdl.constants import NOP


class RamTransactionalTC(SimTestCase):

    def setUp(self):
        SimTestCase.setUp(self)
        self.u = u = RamTransactional()
        u.ID_WIDTH = 0
        u.DATA_WIDTH = 32
        u.ADDR_WIDTH = 16
        u.WORDS_WIDTH = 64
        u.ITEMS = 32

        self.compileSim(u)

    def test_basic(self):
        u = self.u
        TEST_LEN = u.ITEMS
        RAM_WORDS = u.WORDS_WIDTH / u.DATA_WIDTH

        # Skip write phase
        u.r.addr._ag.data.extend([NOP for i in range(0, 10)])
        # Read during writing/flushing -> delays it after write
        u.r.addr._ag.data.extend([(0, i) for i in range(0, 10)])

        testAddr = [(0, i, 0) for i in range(0, TEST_LEN)]
        testInitData = [(i) for i in range(0, TEST_LEN * RAM_WORDS)]
        u.w.addr._ag.data.extend(testAddr)
        u.w.data._ag.data.extend(testInitData)

        testSecondAddr = [(0, i, 1) for i in range(0, TEST_LEN)]
        testSecondData = [(i) for i in reversed(range(0, TEST_LEN * RAM_WORDS))]
        u.w.addr._ag.data.extend(testSecondAddr)
        u.w.data._ag.data.extend(testSecondAddr)

        self.runSim((TEST_LEN + 20) * CLK_PERIOD)

        self.assertSequenceEqual(u.r.data._ag.data, testSecondData, "Read data after flush mismatch")
        self.assertSequenceEqual(u.flush_data.addr._ag.data, testAddr, "Flush addr mismatch")
        self.assertSequenceEqual(u.flush_data.data._ag.data, testInitData, "Flush data mismatch")


RamTransactionalTCs = [
    RamTransactionalTC,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    for tc in RamTransactionalTCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
