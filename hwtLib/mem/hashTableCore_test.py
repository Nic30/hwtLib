#!/usr/bin/env python3)
# -*- coding: utf-8 -*-

from hwt.simulator.agentConnector import valuesToInts
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.logic.crcPoly import CRC_16_CCITT
from hwtLib.mem.hashTableCore import HashTableCore
from pycocotb.constants import CLK_PERIOD
from pycocotb.triggers import Timer
from binascii import crc_hqx
from pyMathBitPrecise.bit_utils import mask


class HashTableCoreTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = HashTableCore(CRC_16_CCITT)
        u.KEY_WIDTH = 16
        u.DATA_WIDTH = 8

        u.LOOKUP_HASH = True
        u.LOOKUP_KEY = True
        return u

    def setUp(self):
        SingleUnitSimTestCase.setUp(self)
        # clean up memory
        mem = self.rtl_simulator.model.table_inst.io.ram_memory
        mem.val = mem.def_val = mem._dtype.from_py(0 for _ in range(mem._dtype.size))

    def test_lookupInEmpty(self):
        u = self.u

        u.lookup._ag.data.extend([0,
                                  self._rand.getrandbits(8),
                                  self._rand.getrandbits(8)])

        self.runSim(15 * CLK_PERIOD)

        for d in u.lookupRes._ag.data:
            found = d[-1]
            self.assertValEqual(found, 0)

    def test_lookupInsertLookup(self, N=16):
        u = self.u
        lookup = u.lookup._ag.data
        lookupRes = u.lookupRes._ag.data
        getrandbits = self._rand.getrandbits

        def get_hash(k: int):
            return crc_hqx(k.to_bytes(u.KEY_WIDTH // 8, "little"),
                           CRC_16_CCITT.INIT) & mask(u.HASH_WIDTH)

        # {hash: (key, data)}
        expected_content = {}

        def insertAndCheck(i):
            ae = self.assertValEqual
            # wait for lookup
            _key = getrandbits(8)
            lookup.append(_key)
            yield Timer(5 * CLK_PERIOD)
            _hash, key, _, found, occupied = lookupRes.popleft()
            h = get_hash(int(key))
            ae(key, _key, i)
            ae(_hash, h, i)
            v = expected_content.get(h, None)
            if v is None:
                ae(found, 0, i)
                ae(occupied, 0, i)
            else:
                ae(found, v[0] == _key, i)
                ae(occupied, 1, i)

            data = getrandbits(8)
            # insert previous lookup with new data
            u.insert._ag.data.append((_hash, key, data, 1))

            yield Timer(5 * CLK_PERIOD)
            expected_content[int(_hash)] = (int(key), int(data))

            # create another key lookup probably not related to prev insert
            key1 = getrandbits(16)
            h = get_hash(key1)
            v = expected_content.get(h, None)
            if v is not None:
                expected1 = (h, key1, v[1], int(v[0] == key1), 1)
            else:
                expected1 = (h, key1, 0, 0, 0)

            lookup.extend([key, key1])
            yield Timer(5 * CLK_PERIOD)
            # hash, key, data, found, occupied
            expected0 = tuple(valuesToInts((_hash, key, data, 1, 1)))

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

            yield Timer(len(expected_content) * 3 * CLK_PERIOD)
            for (h, k, v) in expected:
                _hash, key, _, found, occupied = lookupRes.popleft()
                self.assertValEqual(key, k)
                self.assertValEqual(_hash, h)
                self.assertValEqual(found, True)
                self.assertValEqual(occupied, True)

        self.procs.append(tryInsertNotFoundAndLookupIt())

        self.runSim(N * 30 * CLK_PERIOD)
        self.assertEmpty(u.lookupRes._ag.data)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(HashTableCoreTC('test_lookupInEmpty'))
    suite.addTest(unittest.makeSuite(HashTableCoreTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
