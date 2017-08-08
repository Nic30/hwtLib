from hwt.simulator.simTestCase import SimTestCase
from hwtLib.mem.hashTableCore import HashTableCore
from hwtLib.logic.crcPoly import CRC_32
from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import valuesToInts


class HashTableCoreTC(SimTestCase):

    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u = HashTableCore(CRC_32)
        u.KEY_WIDTH.set(16)
        u.DATA_WIDTH.set(8)

        u.LOOKUP_HASH.set(True)
        u.LOOKUP_KEY.set(True)

        self.prepareUnit(self.u)

        # clean up memory
        mem = self.model.table_inst.ram_memory.defaultVal
        for i in range(mem._dtype.size):
            mem.val[i] = mem._dtype.elmType.fromPy(0)

    def test_lookupInEmpty(self):
        u = self.u

        u.lookup._ag.data.extend([0, self._rand.getrandbits(8), self._rand.getrandbits(8)])

        self.doSim(150 * Time.ns)

        for d in u.lookupRes._ag.data:
            found = d[-1]
            self.assertValEqual(found, 0)

    def test_lookupInsertLookup(self):
        u = self.u
        u.lookup._ag.data.append(self._rand.getrandbits(8))

        def tryInsertNotFoundAndLookupIt(s):
            # wait for lookup
            yield s.wait(50 * Time.ns)
            _hash, key, _, found, occupied = u.lookupRes._ag.data.popleft()
            data = self._rand.getrandbits(8)

            self.assertValEqual(found, False)
            self.assertValEqual(occupied, False)

            u.insert._ag.data.append((_hash, key, data, 1))

            yield s.wait(50 * Time.ns)

            key2 = self._rand.getrandbits(16)
            u.lookup._ag.data.extend([key, key2])
            yield s.wait(50 * Time.ns)

            expected0 = tuple(valuesToInts((_hash, key, data, 1, 1)))
            expected1 = (21, key2, 0, 0, 0)

            self.assertValSequenceEqual(u.lookupRes._ag.data,
                                        [expected0, expected1])

        self.procs.append(tryInsertNotFoundAndLookupIt)

        self.doSim(300 * Time.ns)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HashTableCoreTC('test_lookupInEmpty'))
    suite.addTest(unittest.makeSuite(HashTableCoreTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
