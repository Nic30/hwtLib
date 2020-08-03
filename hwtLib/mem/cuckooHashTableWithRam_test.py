#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.logic.crcPoly import CRC_32
from hwtLib.mem.cuckooHashTablWithRam import CuckooHashTableWithRam
from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer
from hwt.hdl.constants import NOP


class CuckooHashTableWithRamTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = CuckooHashTableWithRam([CRC_32, CRC_32])
        u.KEY_WIDTH = 16
        u.DATA_WIDTH = 8
        u.LOOKUP_KEY = True
        u.TABLE_SIZE = 32 * 2
        cls.TABLE_CNT = len(u.POLYNOMIALS)
        return u

    def setUp(self):
        SingleUnitSimTestCase.setUp(self)
        m = self.rtl_simulator.model
        self.TABLE_MEMS = [getattr(m, "table_cores_%d_inst" % i).table_inst.io.ram_memory
                           for i in range(self.TABLE_CNT)]

    def cleanupMemory(self):
        for mem in self.TABLE_MEMS:
            mem.val = mem.def_val = mem._dtype.from_py([0 for _ in range(mem._dtype.size)])

    def checkContains(self, reference):
        d = self.hashTableAsDict()
        for key, data in d.items():
            self.assertIn(key, reference)
            self.assertValEqual(data, reference[key])
            del reference[key]
        self.assertEqual(reference, {})

    def hashTableAsDict(self):
        d = {}
        SUB_TABLE_SIZE = self.u.TABLE_SIZE // len(self.TABLE_MEMS)
        for t in self.TABLE_MEMS:
            self.assertEqual(len(t), SUB_TABLE_SIZE)
            for i in range(SUB_TABLE_SIZE):
                key, data, item_vld = self.parseItem(t[i].read())
                if item_vld:
                    key = int(key)
                    assert key not in d.keys(), key
                    d[key] = data
        return d

    def parseItem(self, item):
        """
        :return: tuple (key, data, item_vld)
        """
        return self.u.table_cores[0].parseItem(item)

    def test_clean(self):
        u = self.u
        u.clean._ag.data.append(1)
        self.runSim(40 * CLK_PERIOD)
        SUB_TABLE_SIZE = self.u.TABLE_SIZE // len(self.TABLE_MEMS)
        for t in self.TABLE_MEMS:
            self.assertEqual(len(t), SUB_TABLE_SIZE)
            for i in range(SUB_TABLE_SIZE):
                _, _, item_vld = self.parseItem(t[i].read())
                self.assertValEqual(item_vld, 0, i)

    def test_simpleInsert(self):
        u = self.u
        u.clean._ag.data.append(1)
        reference = {56: 11,
                     99: 55,
                     104: 78,
                     15: 79,
                     16: 90}

        def planInsert():
            yield Timer(3 * CLK_PERIOD)
            for k, v in sorted(reference.items(), key=lambda x: x[0]):
                u.insert._ag.data.append((k, v))

        self.procs.append(planInsert())

        self.runSim(65 * CLK_PERIOD)
        self.checkContains(reference)

    def test_simpleInsertAndLookup(self, randomize=False):
        u = self.u
        self.cleanupMemory()
        reference = {
            15: 79,
            16: 90,
            56: 11,
            99: 55,
            104: 78,
        }
        expected = []
        found = 1
        occupied = 1
        u.lookup._ag.data.extend([NOP for _ in range(2*len(reference))])
        for k, v in sorted(reference.items(), key=lambda x: x[0]):
            # insert should have higher priority
            u.insert._ag.data.append((k, v))
            u.lookup._ag.data.append(k)
            expected.append((k, v, found, occupied))
        t = 80
        if randomize:
            self.randomize(u.insert)
            self.randomize(u.lookup)
            self.randomize(u.lookupRes)
            self.randomize(u.delete)
            self.randomize(u.clean)
            t *= 3
            
        self.runSim(t * CLK_PERIOD)
        self.checkContains(reference)
        self.assertValSequenceEqual(u.lookupRes._ag.data, expected)

    def test_simpleInsertAndLookup_randomized(self):
        self.test_simpleInsertAndLookup(randomize=True)

    def test_80p_fill(self):
        u = self.u
        self.cleanupMemory()
        CNT = int(self.u.TABLE_SIZE * 0.8)
        reference = {i + 1: i + 2 for i in range(CNT)}
        for k, v in sorted(reference.items(), key=lambda x: x[0]):
            u.insert._ag.data.append((k, v))

        self.runSim(CNT * 6 * CLK_PERIOD)
        self.checkContains(reference)

    def test_delete(self):
        u = self.u
        self.cleanupMemory()
        reference = {56: 11,
                     99: 55,
                     104: 78,
                     15: 79,
                     16: 90}
        toDelete = [15, 99]

        for k, v in sorted(reference.items(), key=lambda x: x[0]):
            u.insert._ag.data.append((k, v))

        def doDelete():
            yield Timer(35 * CLK_PERIOD)
            u.delete._ag.data.extend(toDelete)
        self.procs.append(doDelete())

        self.runSim(50 * CLK_PERIOD)
        for k in toDelete:
            del reference[k]
        self.checkContains(reference)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(CuckooHashTableWithRamTC('test_lookupInEmpty'))
    suite.addTest(unittest.makeSuite(CuckooHashTableWithRamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
