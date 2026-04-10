#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from hwt.pyUtils.setList import SetList
from ipCorePackager.setList import SetList as SetListIpCorePackager


class SetListTC(unittest.TestCase):
    CLS = SetList

    def test_constructors(self):
        v = self.CLS()
        self.assertFalse(1 in v)
        self.assertFalse(None in v)

        v = self.CLS((1,))
        self.assertEqual(len(v), 1)
        self.assertTrue(1 in v)
        self.assertFalse(2 in v)

        v = self.CLS((1, 3))
        self.assertEqual(len(v), 2)
        self.assertTrue(1 in v)
        self.assertFalse(2 in v)
        self.assertTrue(3 in v)

        v = self.CLS((1, 3, 1))
        self.assertEqual(len(v), 2)
        self.assertTrue(1 in v)
        self.assertFalse(2 in v)
        self.assertTrue(3 in v)

    def test_append(self):
        v = self.CLS()
        v.append(1)
        self.assertEqual(len(v), 1)
        self.assertTrue(1 in v)

        v.append(1)
        self.assertEqual(len(v), 1)
        self.assertTrue(1 in v)

        v.append(2)
        self.assertEqual(len(v), 2)
        self.assertTrue(1 in v)
        self.assertTrue(2 in v)
        self.assertFalse(3 in v)

    def test_extend(self):
        v = self.CLS([1, 2])
        v.extend([])
        self.assertEqual(len(v), 2)
        self.assertTrue(1 in v)
        self.assertTrue(2 in v)

        v.extend([1, 2])
        self.assertEqual(len(v), 2)
        self.assertTrue(1 in v)
        self.assertTrue(2 in v)

        v.extend([1, 2, 3, 4, 1])
        self.assertEqual(len(v), 4)
        self.assertTrue(1 in v)
        self.assertTrue(2 in v)
        self.assertTrue(3 in v)
        self.assertTrue(4 in v)

    def test_setitem(self):
        v = self.CLS([])
        with self.assertRaises(IndexError):
            v[0] = 1

        self.assertEqual(len(v), 0)
        self.assertEqual(len(v._get_set()), 0)

        v = self.CLS([1, 2, 3])
        v[0] = 4

        self.assertEqual(len(v), 3)
        self.assertFalse(1 in v)
        self.assertTrue(2 in v)
        self.assertTrue(3 in v)
        self.assertTrue(4 in v)

        v[0] = 4
        self.assertEqual(len(v), 3)
        self.assertFalse(1 in v)
        self.assertTrue(2 in v)
        self.assertTrue(3 in v)
        self.assertTrue(4 in v)

        v[1] = 5
        self.assertEqual(len(v), 3)
        self.assertFalse(2 in v)
        self.assertTrue(3 in v)
        self.assertTrue(4 in v)
        self.assertTrue(5 in v)

        v = self.CLS([1, 2, 3])
        v[:] = [4, 5, 6, 7]
        self.assertEqual(len(v), 4)
        self.assertFalse(1 in v)
        self.assertTrue(4 in v)
        self.assertTrue(5 in v)
        self.assertTrue(6 in v)
        self.assertTrue(7 in v)

        v = self.CLS([1, 2, 3])
        v[1:] = [4, 5]
        self.assertEqual(len(v), 3)
        self.assertFalse(2 in v)
        self.assertTrue(1 in v)
        self.assertTrue(4 in v)
        self.assertTrue(5 in v)

        v = self.CLS([1, 2, 3])
        v[1:2] = [4, 5]
        self.assertEqual(len(v), 4)
        self.assertFalse(2 in v)
        self.assertTrue(1 in v)
        self.assertTrue(4 in v)
        self.assertTrue(5 in v)
        self.assertTrue(3 in v)

    def test_insert(self):
        v = self.CLS()
        v.insert(0, 1)
        self.assertEqual(len(v), 1)
        self.assertEqual(v, [1])
        self.assertTrue(1 in v)

        v.insert(0, 1)
        self.assertEqual(len(v), 2)
        self.assertEqual(v, [1, 1])
        self.assertTrue(1 in v)

        v.insert(1, 2)
        self.assertEqual(len(v), 3)
        self.assertEqual(v, [1, 2, 1])
        self.assertTrue(1 in v)
        self.assertTrue(2 in v)

        v.insert(100, 3)
        self.assertEqual(len(v), 4)
        self.assertEqual(v, [1, 2, 1, 3])
        self.assertTrue(3 in v)

    def test_intersection_set(self):
        v1 = self.CLS([1, 2, 3])
        v2 = self.CLS([2, 3, 4])
        s = set([2, 3])

        result = v1.intersection_set(v2)
        self.assertEqual(result, s)

    def test_discard(self):
        v = self.CLS([1, 2, 3])
        self.assertTrue(v.discard(2))
        self.assertEqual(len(v), 2)
        self.assertFalse(2 in v)
        self.assertTrue(1 in v)
        self.assertTrue(3 in v)

        self.assertFalse(v.discard(2))
        self.assertEqual(len(v), 2)

    def test_remove(self):
        v = self.CLS([1, 2, 3])
        v.remove(2)
        self.assertEqual(len(v), 2)
        self.assertFalse(2 in v)
        self.assertTrue(1 in v)
        self.assertTrue(3 in v)

        with self.assertRaises(ValueError):
            v.remove(2)

    def test_pop(self):
        v = self.CLS([1, 2, 3])
        item = v.pop()
        self.assertEqual(item, 3)
        self.assertEqual(len(v), 2)
        self.assertFalse(3 in v)

        item = v.pop(0)
        self.assertEqual(item, 1)
        self.assertEqual(len(v), 1)
        self.assertFalse(1 in v)

    def test_clear(self):
        v = self.CLS([1, 2, 3])
        v.clear()
        self.assertEqual(len(v), 0)
        self.assertFalse(1 in v)
        self.assertFalse(2 in v)
        self.assertFalse(3 in v)

    def test_copy(self):
        v = self.CLS([1, 2, 3])
        c = v.copy()
        self.assertEqual(len(c), 3)
        self.assertTrue(1 in c)
        self.assertTrue(2 in c)
        self.assertTrue(3 in c)
        self.assertIsNot(v, c)

        v.append(4)
        self.assertEqual(len(c), 3)
        self.assertFalse(4 in c)


class SetListIpCorePackagerTC(SetListTC):
    CLS = SetListIpCorePackager

    def test_setitem(self):
        v = self.CLS([])
        with self.assertRaises(NotImplementedError):
            v[0] = 1


class SetDequeTC(SetListTC):
    CLS = SetListIpCorePackager

    def test_setitem(self):
        SetListIpCorePackagerTC.test_setitem(self)


if __name__ == "__main__":
    testLoader = unittest.TestLoader()

    suite = unittest.TestSuite([testLoader.loadTestsFromTestCase(tc) for tc in [SetListTC, SetListIpCorePackagerTC, SetDequeTC]])
    # suite = unittest.TestSuite([SetListTC("test_constructors")])
    # suite = testLoader.loadTestsFromTestCase(SetListTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
