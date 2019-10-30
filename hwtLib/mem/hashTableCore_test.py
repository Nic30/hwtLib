#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.agentConnector import valuesToInts
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.logic.crcPoly import CRC_32
from hwtLib.mem.hashTableCore import HashTableCore
from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer


class HashTableCoreTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = HashTableCore(CRC_32)
        u.KEY_WIDTH = 16
        u.DATA_WIDTH = 8

        u.LOOKUP_HASH = True
        u.LOOKUP_KEY = True
        return u

    def setUp(self):
        SingleUnitSimTestCase.setUp(self)
        # clean up memory
        mem = self.rtl_simulator.model.table_inst.io.ram_memory.def_val
        for i in range(mem._dtype.size):
            mem.val[i] = mem._dtype.element_t.from_py(0)

    def test_lookupInEmpty(self):
        u = self.u

        u.lookup._ag.data.extend([0,
                                  self._rand.getrandbits(8),
                                  self._rand.getrandbits(8)])

        self.runSim(15 * CLK_PERIOD)

        for d in u.lookupRes._ag.data:
            found = d[-1]
            self.assertValEqual(found, 0)

    def test_lookupInsertLookup(self):
        u = self.u
        u.lookup._ag.data.append(self._rand.getrandbits(8))

        def tryInsertNotFoundAndLookupIt():
            # wait for lookup
            yield Timer(5 * CLK_PERIOD)
            _hash, key, _, found, occupied = u.lookupRes._ag.data.popleft()
            data = self._rand.getrandbits(8)

            self.assertValEqual(found, False)
            self.assertValEqual(occupied, False)

            u.insert._ag.data.append((_hash, key, data, 1))

            yield Timer(5 * CLK_PERIOD)

            key2 = self._rand.getrandbits(16)
            u.lookup._ag.data.extend([key, key2])
            yield Timer(5 * CLK_PERIOD)

            expected0 = tuple(valuesToInts((_hash, key, data, 1, 1)))
            expected1 = (14, key2, 0, 0, 0)

            self.assertValSequenceEqual(u.lookupRes._ag.data,
                                        [expected0, expected1])

        self.procs.append(tryInsertNotFoundAndLookupIt())

        self.runSim(30 * CLK_PERIOD)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HashTableCoreTC('test_lookupInEmpty'))
    suite.addTest(unittest.makeSuite(HashTableCoreTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
