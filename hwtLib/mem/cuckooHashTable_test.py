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
        u.TABLE_SIZE.set(self.TABLE_SIZE)
        self.prepareUnit(u)
        self.TABLE_MEMS = [getattr(self.model, "table%d_inst" % i).table_inst.ram_memory._val.val
                           for i in range(2)]

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
        self.doSim(400 * Time.ns)
        for t in self.TABLE_MEMS:
            self.assertEqual(len(t), self.TABLE_SIZE)
            for i in range(self.TABLE_SIZE):
                _, _, vldFlag = self.parseItem(t[i])
                self.assertValEqual(vldFlag, 0, i)



if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(CuckooHashTableTC('test_lookupInEmpty'))
    suite.addTest(unittest.makeSuite(CuckooHashTableTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
