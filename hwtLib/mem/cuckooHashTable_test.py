from hwt.simulator.simTestCase import SimTestCase
from hwtLib.logic.crcPoly import CRC_32
from hwtLib.mem.cuckooHashTable import CuckooHashTable
from hwt.hdlObjects.constants import Time


class CuckooHashTableTC(SimTestCase):
    def setUp(self):
        SimTestCase.setUp(self)
        self.TABLE_SIZE = 32
        u = self.u = CuckooHashTable([CRC_32, CRC_32])
        u.KEY_WIDTH.set(16)
        u.DATA_WIDTH.set(8)
        u.LOOKUP_KEY.set(True)
        u.TABLE_SIZE.set(self.TABLE_SIZE)
        self.TABLE_CNT = 2
        self.prepareUnit(u)
        self.TABLE_MEMS = [getattr(self.model, "table%d_inst" % i).table_inst.ram_memory._val.val
                           for i in range(self.TABLE_CNT)]

    def cleanupMemory(self):
        for ti in range(self.TABLE_CNT):
            table = getattr(self.model, "table%d_inst" % ti).table_inst
            mem = table.ram_memory.defaultVal
            for i in range(mem._dtype.size):
                mem.val[i] = mem._dtype.elmType.fromPy(0)

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
                key, data, vldFlag = self.parseItem(t[i])
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
        self.doSim(400 * Time.ns)
        for t in self.TABLE_MEMS:
            self.assertEqual(len(t), self.TABLE_SIZE)
            for i in range(self.TABLE_SIZE):
                _, _, vldFlag = self.parseItem(t[i])
                self.assertValEqual(vldFlag, 0, i)

    def test_simpleInsert(self):
        u = self.u
        u.clean._ag.data.append(1)
        reference = {56: 11,
                     99: 55,
                     104: 78,
                     15: 79,
                     16: 90}

        def planInsert(sim):
            yield sim.wait(30 * Time.ns)
            for k, v in sorted(reference.items(), key=lambda x: x[0]):
                u.insert._ag.data.append((k, v))

        self.procs.append(planInsert)

        self.doSim(650 * Time.ns)
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

        self.doSim(800 * Time.ns)
        self.checkContains(reference)
        self.assertValSequenceEqual(u.lookupRes._ag.data, expected)

    def test_80p_fill(self):
        u = self.u
        self.cleanupMemory()
        CNT = int(self.TABLE_SIZE * self.TABLE_CNT * 0.8)
        reference = {i + 1: i + 2 for i in range(CNT)}
        for k, v in sorted(reference.items(), key=lambda x: x[0]):
            u.insert._ag.data.append((k, v))

        self.doSim(CNT * 60 * Time.ns)
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

        def doDelete(sim):
            yield sim.wait(350 * Time.ns)
            u.delete._ag.data.extend(toDelete)
        self.procs.append(doDelete)

        self.doSim(500 * Time.ns)
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
