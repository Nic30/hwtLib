#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import copy

from hwt.hdl.constants import NOP
from hwt.serializer.combLoopAnalyzer import CombLoopAnalyzer
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.errors.combLoops import freeze_set_of_sets
from hwtLib.logic.crcPoly import CRC_32, CRC_32C
from hwtLib.mem.cuckooHashTablWithRam import CuckooHashTableWithRam
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer


class CuckooHashTableWithRam_common_TC(SimTestCase):

    def setUp(self):
        SimTestCase.setUp(self)
        m = self.rtl_simulator.model
        self.TABLE_MEMS = [getattr(m, f"table_cores_{i:d}_inst").table_inst.io.ram_memory
                           for i in range(len(self.u.POLYNOMIALS))]

    def test_no_comb_loops(self):
        s = CombLoopAnalyzer()
        s.visit_Unit(self.u)
        comb_loops = freeze_set_of_sets(s.report())
        # for loop in comb_loops:
        #     print(10 * "-")
        #     for s in loop:
        #         print(s.resolve()[1:])

        self.assertEqual(comb_loops, frozenset())

    def cleanupMemory(self):
        for mem in self.TABLE_MEMS:
            mem.val = mem.def_val = mem._dtype.from_py([0 for _ in range(mem._dtype.size)])

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

    def checkContains(self, reference, data=None):
        reference = copy(reference)
        if data is None:
            data = self.hashTableAsDict()
        self.assertDictEqual({int(k): int(v) for k, v in data.items() }, reference)
        # for key, d in data.items():
        #    self.assertIn(key, reference)
        #    self.assertValEqual(d, reference[key])
        #    del reference[key]
        # self.assertEqual(reference, {})

    def parseItem(self, item):
        """
        :return: tuple (key, data, item_vld)
        """
        return self.u.table_cores[0].parseItem(item)

    def randomize_all(self):
        u = self.u
        self.randomize(u.insert)
        self.randomize(u.insertRes)
        self.randomize(u.lookup)
        self.randomize(u.lookupRes)
        self.randomize(u.delete)
        self.randomize(u.clean)


class CuckooHashTableWithRamTC(CuckooHashTableWithRam_common_TC):

    @classmethod
    def setUpClass(cls):
        u = CuckooHashTableWithRam([CRC_32, CRC_32])
        u.KEY_WIDTH = 16
        u.DATA_WIDTH = 8
        u.LOOKUP_KEY = True
        u.TABLE_SIZE = 32 * 2
        cls.compileSim(u)

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
        reference = {
            56: 11,
            99: 55,
            105: 78,
            15: 79,
            16: 90
        }

        u.clean._ag.data.append(1)

        def planInsert():
            # wait because we want to execute clean first
            yield Timer(3 * CLK_PERIOD)
            for k, v in sorted(reference.items(), key=lambda x: x[0]):
                u.insert._ag.data.append((k, v))

        self.procs.append(planInsert())

        self.runSim(65 * CLK_PERIOD)
        self.assertValSequenceEqual(
            [d[0] for d in u.insertRes._ag.data],
            [0 for _ in range(len(reference))])
        self.checkContains(reference)

    def test_simpleInsertAndLookup(self, randomize=False):
        u = self.u
        self.cleanupMemory()
        reference = {
            15: 79,
            16: 90,
            56: 11,
            99: 55,
            105: 78,
        }
        expected = []
        found = 1
        occupied = 1

        lookup_delay = 2 * len(reference)
        if randomize:
            lookup_delay *= 3

        u.lookup._ag.data.extend([NOP for _ in range(lookup_delay)])

        for k, v in sorted(reference.items(), key=lambda x: x[0]):
            # insert should have higher priority
            u.insert._ag.data.append((k, v))
            u.lookup._ag.data.append(k)
            expected.append((k, v, found, occupied))

        t = 80
        if randomize:
            self.randomize_all()
            t *= 3

        self.runSim(t * CLK_PERIOD)
        self.checkContains(reference)
        self.assertValSequenceEqual([d[0] for d in u.insertRes._ag.data],
                                    [0 for _ in range(len(reference))])
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

        self.runSim(CNT * 7 * CLK_PERIOD)
        self.checkContains(reference)

    def test_delete(self):
        u = self.u
        self.cleanupMemory()
        reference = {
            15: 79,
            16: 90,
            56: 11,
            99: 55,
            105: 78,
        }
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


class CuckooHashTableWithRam_1TableTC(CuckooHashTableWithRamTC):

    @classmethod
    def setUpClass(cls):
        u = CuckooHashTableWithRam([CRC_32])
        u.KEY_WIDTH = 16
        u.DATA_WIDTH = 8
        u.LOOKUP_KEY = True
        u.TABLE_SIZE = 32
        u.MAX_REINSERT = 1
        cls.compileSim(u)


class CuckooHashTableWithRam_2Table_collisionTC(CuckooHashTableWithRam_common_TC):

    @classmethod
    def setUpClass(cls):
        u = CuckooHashTableWithRam([CRC_32, CRC_32C])
        u.KEY_WIDTH = 8
        u.DATA_WIDTH = 8
        u.LOOKUP_KEY = True
        u.TABLE_SIZE = 2 * 2
        u.MAX_REINSERT = 4
        cls.compileSim(u)

    def test_nop(self):
        self.randomize_all()
        self.runSim(50 * CLK_PERIOD)
        self.assertEmpty(self.u.lookupRes._ag.data)

    def test_insert_coliding(self, N=10, randomized=False):
        if randomized:
            self.randomize_all()
        self.cleanupMemory()

        u = self.u
        reference = {i + 1: i + 2 for i in range(N)}
        for k, v in sorted(reference.items(), key=lambda x: x[0]):
            u.insert._ag.data.append((k, v))

        t = N
        if randomized:
            t *= 3

        self.runSim((15 * t + 10) * CLK_PERIOD)
        self.assertEmpty(u.lookupRes._ag.data)

        table = self.hashTableAsDict()
        self.assertGreater(len(table), 0)
        self.assertEqual(len(u.insertRes._ag.data), N)
        for pop, key, data in u.insertRes._ag.data:
            if pop:
                key = int(key)
                self.assertNotIn(key, table)
                table[key] = data

        self.checkContains(reference, table)

    def test_insert_coliding_randomized(self, N=10):
        self.test_insert_coliding(N=N, randomized=True)


CuckooHashTableWithRamTCs = [
    CuckooHashTableWithRamTC,
    CuckooHashTableWithRam_1TableTC,
    CuckooHashTableWithRam_2Table_collisionTC,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(CuckooHashTableWithRam_2Table_collisionTC('test_insert_coliding'))
    for tc in CuckooHashTableWithRamTCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
