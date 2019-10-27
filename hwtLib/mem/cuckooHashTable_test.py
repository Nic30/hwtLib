#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.logic.crcPoly import CRC_32
from hwtLib.mem.cuckooHashTable import CuckooHashTable
from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer


class CuckooHashTableTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.TABLE_SIZE = 32
        u = CuckooHashTable([CRC_32, CRC_32])
        u.KEY_WIDTH = 16
        u.DATA_WIDTH = 8
        u.LOOKUP_KEY = True
        u.TABLE_SIZE = cls.TABLE_SIZE
        cls.TABLE_CNT = 2
        return u

    def setUp(self):
        SingleUnitSimTestCase.setUp(self)
        m = self.rtl_simulator.model
        self.TABLE_MEMS = [getattr(m, "tables_%d_inst" % i).table_inst.io.ram_memory
                           for i in range(self.TABLE_CNT)]

    def cleanupMemory(self):
        for mem in self.TABLE_MEMS:
            mem = mem.def_val
            for i in range(mem._dtype.size):
                mem.val[i] = mem._dtype.element_t.from_py(0)

    def checkContains(self, reference):
        d = self.hashTableAsDict()
        for key, data in d.items():
            self.assertIn(key, reference)
            self.assertValEqual(data, reference[key])
            del reference[key]
        self.assertEqual(reference, {})

    def hashTableAsDict(self):
        d = {}
        for t in self.TABLE_MEMS:
            self.assertEqual(len(t), self.TABLE_SIZE)
            for i in range(self.TABLE_SIZE):
                key, data, vldFlag = self.parseItem(t[i].read())
                if vldFlag:
                    key = int(key)
                    d[key] = data
        return d

    def parseItem(self, item):
        """
        :return: tuple (key, data, vldFlag)
        """
        return self.u.tables[0].parseItem(item)

    def test_clean(self):
        u = self.u
        u.clean._ag.data.append(1)
        self.runSim(40 * CLK_PERIOD)
        for t in self.TABLE_MEMS:
            self.assertEqual(len(t), self.TABLE_SIZE)
            for i in range(self.TABLE_SIZE):
                _, _, vldFlag = self.parseItem(t[i].read())
                self.assertValEqual(vldFlag, 0, i)

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

    def test_simpleInsertAndLookup(self):
        u = self.u
        self.cleanupMemory()
        reference = {56: 11,
                     99: 55,
                     104: 78,
                     15: 79,
                     16: 90}
        expected = []
        found = 1
        occupied = 1
        for k, v in sorted(reference.items(), key=lambda x: x[0]):
            u.insert._ag.data.append((k, v))
            u.lookup._ag.data.append(k)
            expected.append((k, v, found, occupied))

        self.runSim(80 * CLK_PERIOD)
        self.checkContains(reference)
        self.assertValSequenceEqual(u.lookupRes._ag.data, expected)

    def test_80p_fill(self):
        u = self.u
        self.cleanupMemory()
        CNT = int(self.TABLE_SIZE * self.TABLE_CNT * 0.8)
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
    # suite.addTest(CuckooHashTableTC('test_lookupInEmpty'))
    suite.addTest(unittest.makeSuite(CuckooHashTableTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
