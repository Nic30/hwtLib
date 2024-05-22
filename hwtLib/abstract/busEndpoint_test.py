#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hwIOs.hwIO_map import HTypeFromHwIOObjMap, HwIOObjMap
from hwt.hwIOs.std import HwIORegCntrl, HwIOVectSignal, HwIODataVld
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.struct import HStruct, HStructFieldMeta


# example methods for interface construction
def mk_regCntr(name, width):
    a = HwIORegCntrl()
    a.DATA_WIDTH = width
    a._name = name
    a._loadDeclarations()
    return a


def mk_sig(name, width):
    a = HwIOVectSignal(width)
    a._name = name
    a._loadDeclarations()
    return a


def mk_vldSynced(name, width):
    a = HwIODataVld()
    a.DATA_WIDTH = width
    a._name = name
    a._loadDeclarations()
    return a


class BusEndpointTC(unittest.TestCase):

    def test_HTypeFromHwIOMap_Struct(self):
        DATA_WIDTH = 32

        t = HTypeFromHwIOObjMap(
            HwIOObjMap([
                    mk_regCntr("a", DATA_WIDTH),
                    mk_regCntr("b", DATA_WIDTH),
                    mk_sig("c", DATA_WIDTH),
                    mk_vldSynced("d", DATA_WIDTH),
            ]))

        _t = HBits(DATA_WIDTH)
        self.assertEqual(t, HStruct(
                (_t, "a"),
                (_t, "b"),
                (_t, "c"),
                (_t, "d"),
            ))

    def test_HTypeFromHwIOMap_Padding(self):
        DATA_WIDTH = 32

        t = HTypeFromHwIOObjMap(
            HwIOObjMap([
                mk_regCntr("a", DATA_WIDTH),
                mk_regCntr("b", DATA_WIDTH),
                mk_sig("c", DATA_WIDTH),
                (HBits(4 * DATA_WIDTH), None),
                mk_vldSynced("d", DATA_WIDTH),
            ]))
        _t = HBits(DATA_WIDTH)
        t2 = HStruct(
                (_t, "a"),
                (_t, "b"),
                (_t, "c"),
                (HBits(4 * DATA_WIDTH), None),
                (_t, "d"),
            )

        self.assertEqual(t, t2)

    def test_HTypeFromHwIOMap_Array(self):
        DATA_WIDTH = 32

        t = HTypeFromHwIOObjMap(
            HwIOObjMap([
                mk_regCntr("a", DATA_WIDTH),
                (HBits(4 * DATA_WIDTH), None),
                ([mk_vldSynced("d", DATA_WIDTH) for _ in range(4)], "ds")
            ]))

        _t = HBits(DATA_WIDTH)
        t2 = HStruct(
                (_t, "a"),
                (HBits(4 * DATA_WIDTH), None),
                (_t[4], "ds", HStructFieldMeta(split=True)),
            )
        self.assertEqual(t, t2)

    def test_HTypeFromHwIOMap_ArrayOfStructs(self):
        DATA_WIDTH = 32

        t = HTypeFromHwIOObjMap(
            HwIOObjMap([
                mk_regCntr("a", DATA_WIDTH),
                (HBits(4 * DATA_WIDTH), None),
                ([HwIOObjMap([
                    mk_vldSynced("c", DATA_WIDTH),
                    mk_vldSynced("d", DATA_WIDTH)
                ]) for _ in range(4)], "ds")
            ]))

        _t = HBits(DATA_WIDTH)
        _t2 = HStruct(
                (_t, "c"),
                (_t, "d")
            )
        t2 = HStruct(
                (_t, "a"),
                (HBits(4 * DATA_WIDTH), None),
                (_t2[4], "ds", HStructFieldMeta(split=True)),
            )

        self.assertEqual(t, t2)

    def test_HTypeFromHwIOMap_ArrayOfStructsOfStructs(self):
        DATA_WIDTH = 32
        m = HwIOObjMap([
                mk_regCntr("a", DATA_WIDTH),
                (HBits(4 * DATA_WIDTH), None),
                ([HwIOObjMap([
                    (HwIOObjMap([
                       mk_vldSynced("c", DATA_WIDTH),
                       mk_vldSynced("d", DATA_WIDTH)
                    ]), "nested")
                ]) for _ in range(4)], "ds")
            ])

        t = HTypeFromHwIOObjMap(m)

        _t = HBits(DATA_WIDTH)
        _t2 = HStruct(
            (HStruct((_t, "c"),
                     (_t, "d")), "nested", HStructFieldMeta(split=True)))
        t2 = HStruct(
                (_t, "a"),
                (HBits(4 * DATA_WIDTH), None),
                (_t2[4], "ds", HStructFieldMeta(split=True)),
            )

        self.assertEqual(t, t2)

    def test_HTypeFromHwIOMap_StructArray(self):
        DATA_WIDTH = 32

        t = HTypeFromHwIOObjMap(
            HwIOObjMap([
                mk_regCntr("a", DATA_WIDTH),
                (HBits(4 * DATA_WIDTH), None),
                ([
                    HwIOObjMap([
                        mk_vldSynced("d", DATA_WIDTH),
                        mk_sig("e", DATA_WIDTH),
                        (HBits(DATA_WIDTH * 2), None),
                        mk_sig("f", DATA_WIDTH),
                    ]) for _ in range(4)], "ds")
            ]))

        _t = HBits(DATA_WIDTH)
        expected_t = HStruct(
            (_t, "a"),
            (HBits(4 * DATA_WIDTH), None),
            (HStruct(
                (_t, "d"),
                (_t, "e"),
                (HBits(2 * DATA_WIDTH), None),
                (_t, "f"),
                )[4], "ds", HStructFieldMeta(split=True)),
        )
        self.assertEqual(t, expected_t)

    def test_HTypeFromHwIOMap_wrongArray(self):
        DATA_WIDTH = 32
        with self.assertRaises(AssertionError):
            HTypeFromHwIOObjMap(
                HwIOObjMap([
                    ([mk_sig("e", DATA_WIDTH),
                      mk_sig("e", 2 * DATA_WIDTH),
                      ], "ds")
                ]))


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([BusEndpointTC("test_HTypeFromHwIOMap_ArrayOfStructsOfStructs")])
    suite = testLoader.loadTestsFromTestCase(BusEndpointTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
