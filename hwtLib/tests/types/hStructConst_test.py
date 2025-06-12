#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwtLib.types.net.dpdk import rte_mbuf
from hwtLib.types.net.udp import UDP_header_t
from hwt.hdl.types.struct import HStruct
from hwtLib.types.ctypes import uint8_t


class HStructConstTC(unittest.TestCase):

    def test_structFromPy(self):
        v = rte_mbuf.from_py({
                         "buf_len": 10,
                         "seqn": 1,
                         })
        self.assertEqual(int(v.buf_len), 10)
        self.assertEqual(int(v.seqn), 1)

    def test_tryToSetNonExistingDefVal(self):
        with self.assertRaises(AssertionError):
            UDP_header_t.from_py({
                                 "wrong": 10
                                 })

    def test_tryToSetNonExistingAttribute(self):
        v = rte_mbuf.from_py({
                         "buf_len": 10,
                         "seqn": 1,
                         })

        with self.assertRaises(AttributeError):
            v.nonExisting = None

    def test_HStructArray(self):
        elmTy = uint8_t
        t = HStruct(
            (elmTy, "x"),
            (elmTy, "y"),
        )

        v = t[4].from_py([
            (0, 1),
            (2, 3),
            (4, 5),
            (6, 7),
        ])

        self.assertEqual(int(v[0].x), 0)
        self.assertEqual(int(v[1].x), 2)
        self.assertEqual(int(v[3].x), 6)

        self.assertEqual(int(v[0].y), 1)
        self.assertEqual(int(v[1].y), 3)
        self.assertEqual(int(v[3].y), 7)
    
    #def test_HStruct_withHArray(self):
    #    t = HStruct(
    #        (uint8_t[4], "data")
    #    )
    #    
    #    self.
        
        

if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HStructConstTC("test_sWithStartPadding")])
    suite = testLoader.loadTestsFromTestCase(HStructConstTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
