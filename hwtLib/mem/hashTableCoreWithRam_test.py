#!/usr/bin/env python3)
# -*- coding: utf-8 -*-

from binascii import crc_hqx

from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import valuesToInts
from hwtLib.logic.crcPoly import CRC_16_CCITT
from hwtLib.mem.hashTableCoreWithRam import HashTableCoreWithRam
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer
from pyMathBitPrecise.bit_utils import mask


class HashTableCoreWithRamTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = HashTableCoreWithRam(CRC_16_CCITT)
        u.KEY_WIDTH = 16
        u.DATA_WIDTH = 8

        u.LOOKUP_HASH = True
        u.LOOKUP_KEY = True
        cls.compileSim(u)

    def setUp(self):
        SimTestCase.setUp(self)
        # clean up memory
        mem = self.rtl_simulator.model.table_inst.io.ram_memory
        mem.val = mem.def_val = mem._dtype.from_py(0 for _ in range(mem._dtype.size))

    def test_lookupInEmpty(self):
        u = self.u

        u.io.lookup._ag.data.extend([0,
                                  self._rand.getrandbits(8),
                                  self._rand.getrandbits(8)])

        self.runSim(15 * CLK_PERIOD)

        for d in u.io.lookupRes._ag.data:
            found = d[-1]
            self.assertValEqual(found, 0)

    def test_lookupInsertLookup(self, N=16, randomized=False):
        u = self.u
        t_factor = CLK_PERIOD
        if randomized:
            self.randomize(u.io.lookup)
            self.randomize(u.io.lookupRes)
            self.randomize(u.io.insert)
            t_factor *= 3

        lookup = u.io.lookup._ag.data
        lookupRes = u.io.lookupRes._ag.data
        getrandbits = self._rand.getrandbits

        def get_hash(k: int):
            return crc_hqx(k.to_bytes(u.KEY_WIDTH // 8, "little"),
                           CRC_16_CCITT.INIT) & mask(u.io.HASH_WIDTH)

        # {hash: (key, data)}
        expected_content = {}

        def insertAndCheck(i):
            ae = self.assertValEqual
            # wait for lookup
            key0 = getrandbits(8)
            lookup.append(key0)
            while not lookupRes:
                yield Timer(t_factor)
            hash0, key, _, found, occupied = lookupRes.popleft()
            hash0 = int(hash0)
            h =  get_hash(key0)
            if occupied:
                h2 = get_hash(int(key))
                ae(h2, h, (i, key0, key))
                ae(hash0, h, (i, key0, key))

            v = expected_content.get(h, None)
            if v is None:
                ae(found, 0, i)
                ae(occupied, 0, i)
            else:
                ae(found, v[0] == key0, i)
                ae(occupied, 1, i)

            data = getrandbits(8)
            # insert previous lookup with new data
            u.io.insert._ag.data.append((hash0, key0, data, 1))

            yield Timer(3 * t_factor)
            expected_content[hash0] = (key0, data)

            # create another key lookup probably not related to prev insert
            key1 = getrandbits(16)
            h = get_hash(key1)
            v = expected_content.get(h, None)
            if v is not None:
                expected1 = (h, v[0], v[1], int(v[0] == key1), 1)
            else:
                expected1 = (h, 0, 0, 0, 0)

            lookup.extend([key0, key1])
            # hash, key, data, found, occupied
            expected0 = tuple(valuesToInts((hash0, key0, data, 1, 1)))
            while len(lookupRes) < 2:
                yield Timer(t_factor)
            d0, d1 = [lookupRes.popleft() for _ in range(2)]
            self.assertValSequenceEqual([d0, d1],
                                        [expected0, expected1])

        def tryInsertNotFoundAndLookupIt():
            for i in range(N):
                yield from insertAndCheck(i)
            expected = []
            for h, (k, v) in expected_content.items():
                lookup.append(k)
                expected.append((h, k, v))

            yield Timer(len(expected_content) * 3 * t_factor)
            for (h, k, v) in expected:
                _hash, key, _, found, occupied = lookupRes.popleft()
                self.assertValEqual(key, k)
                self.assertValEqual(_hash, h)
                self.assertValEqual(found, True)
                self.assertValEqual(occupied, True)

        self.procs.append(tryInsertNotFoundAndLookupIt())

        self.runSim(N * 20 * t_factor)
        self.assertValSequenceEqual(u.io.lookupRes._ag.data, [])

    def test_lookupInsertLookup_randomized(self, N=16):
        self.test_lookupInsertLookup(N, randomized=True)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    #suite.addTest(HashTableCoreWithRamTC('test_lookupInsertLookup_randomized'))
    suite.addTest(unittest.makeSuite(HashTableCoreWithRamTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
