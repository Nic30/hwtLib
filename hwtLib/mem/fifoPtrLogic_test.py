#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import BIT
from hwt.math import log2ceil
from hwtLib.mem.fifoPtrLogic import FifoPtrLogic


class FifoLogicTC(unittest.TestCase):

    def test_ptr_distance_depth8(self, DEPTH: int=8):
        fifoPtrs = FifoPtrLogic(None, DEPTH)
        index_t = fifoPtrs.index_t.from_py
        # ptr0 <= ptr1
        for ptr0 in range(DEPTH):
            _ptr0 = index_t(ptr0)
            for ptr1 in range(ptr0, DEPTH):
                _ptr1 = index_t(ptr1)
                _dist = fifoPtrs._fifo_ptr_distance(_ptr0, _ptr1)
                dist = int(_dist)
                self.assertEqual(dist, ptr1 - ptr0, (ptr0, ptr1))

        # ptr0 > ptr1
        for ptr1 in range(DEPTH - 1):
            _ptr1 = index_t(ptr1)
            for ptr0 in range(ptr1 + 1, DEPTH):
                _ptr0 = index_t(ptr0)
                _dist = fifoPtrs._fifo_ptr_distance(_ptr0, _ptr1)
                dist = int(_dist)
                self.assertEqual(dist, (DEPTH - ptr0) + ptr1, (ptr0, ptr1))

    def test_ptr_distance_depth3(self):
        self.test_ptr_distance_depth8(DEPTH=3)

    def test_ptr_distance_depth4(self):
        self.test_ptr_distance_depth8(DEPTH=4)

    def test_ptr_distance_depth7(self):
        self.test_ptr_distance_depth8(DEPTH=7)

    def test_ptr_distance_depth9(self):
        self.test_ptr_distance_depth8(DEPTH=9)

    def test_is_fifo_ptr_add_possible_depth8(self, DEPTH=8):
        fifoPtrs = FifoPtrLogic(None, DEPTH)
        index_t = fifoPtrs.index_t.from_py
        b = BIT.from_py
        for ptr0 in range(DEPTH):
            _ptr0 = index_t(ptr0)
            for ptr1 in range(DEPTH):
                _ptr1 = index_t(ptr1)
                for useIntForIncrVal in range(2):
                    for incrVal in range(DEPTH):
                        if useIntForIncrVal:
                            if incrVal == 0:
                                continue
                            if DEPTH % incrVal == 0 and ptr0 % incrVal != 0:
                                # skip because the ptr0 is always incremented by incrVal
                                # and due to modulo mapping ptr0 can never have this value
                                continue
                            _incrVal = incrVal

                        else:
                            _incrVal = index_t(incrVal)

                        for allow_eq in range(1, -1, -1):
                            _allow_eq = b(allow_eq)
                            dist = int(fifoPtrs._fifo_ptr_distance(_ptr0, _ptr1))
                            if dist == 0 and allow_eq:
                                dist = DEPTH
                            debugmsg = (ptr0, ptr1, incrVal, allow_eq, useIntForIncrVal)

                            _addPossible, _wouldCross0 = fifoPtrs._is_fifo_ptr_add_possible(_ptr0, _ptr1, _allow_eq, _incrVal)
                            addPossible = bool(_addPossible)
                            wouldCross0 = bool(_wouldCross0)
                            self.assertEqual(addPossible, dist != 0 and dist >= incrVal, debugmsg)
                            self.assertEqual(wouldCross0, ptr0 + incrVal >= DEPTH, debugmsg)

    def test_is_fifo_ptr_add_possible_depth3(self):
        self.test_is_fifo_ptr_add_possible_depth8(3)

    def test_is_fifo_ptr_add_possible_depth4(self):
        self.test_is_fifo_ptr_add_possible_depth8(4)

    def test_is_fifo_ptr_add_possible_depth7(self):
        self.test_is_fifo_ptr_add_possible_depth8(7)

    def test_is_fifo_ptr_add_possible_depth9(self):
        self.test_is_fifo_ptr_add_possible_depth8(9)

    def test_uadd_with_modulo_depth8(self, DEPTH=8):
        fifoPtrs = FifoPtrLogic(None, DEPTH)
        t = fifoPtrs.index_t.from_py
        # res = fifoPtrs._uadd_with_modulo(t(1), t(5))
        for v in range(DEPTH):
            _v = t(v)
            for incrVal in range(DEPTH):
                _incrVal = t(incrVal)
                res = fifoPtrs._uadd_with_modulo(_v, _incrVal)
                self.assertEqual(int(res), (v + incrVal) % DEPTH, (v, incrVal))

    def test_uadd_with_modulo_depth6(self):
        self.test_uadd_with_modulo_depth8(6)

    def test_uadd_with_modulo_depth7(self):
        self.test_uadd_with_modulo_depth8(7)

    def test_uadd_with_modulo_depth9(self):
        self.test_uadd_with_modulo_depth8(9)

    def test_usub_with_modulo_depth8(self, DEPTH=8):
        fifoPtrs = FifoPtrLogic(None, DEPTH)
        t = fifoPtrs.index_t.from_py
        for v in range(DEPTH):
            _v = t(v)
            for incrVal in range(DEPTH):
                _incrVal = t(incrVal)
                res = fifoPtrs._uadd_with_modulo(_v, _incrVal)
                self.assertEqual(int(res), (v + incrVal) % DEPTH)

    def test_usub_with_modulo_depth6(self):
        self.test_usub_with_modulo_depth8(6)

    def test_usub_with_modulo_depth7(self):
        self.test_usub_with_modulo_depth8(7)

    def test_usub_with_modulo_depth9(self):
        self.test_usub_with_modulo_depth8(9)

    def test_uadd_with_modulo_depth4(self):
        self.test_uadd_with_modulo_depth8(4)


FifoPtrLogicc_TCs = [
    FifoLogicTC
]

if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    suite = unittest.TestSuite([testLoader.loadTestsFromTestCase(tc) for tc in FifoPtrLogicc_TCs])
    # suite = unittest.TestSuite([FifoLogicTC("test_usub_with_modulo_depth6")])
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
