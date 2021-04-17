#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct, HStructFieldMeta
from hwt.interfaces.intf_map import HTypeFromIntfMap, IntfMap
from hwt.interfaces.std import RegCntrl, VectSignal, VldSynced


# example methods for interface construction
def mk_regCntr(name, width):
    a = RegCntrl()
    a.DATA_WIDTH = width
    a._name = name
    a._loadDeclarations()
    return a


def mk_sig(name, width):
    a = VectSignal(width)
    a._name = name
    a._loadDeclarations()
    return a


def mk_vldSynced(name, width):
    a = VldSynced()
    a.DATA_WIDTH = width
    a._name = name
    a._loadDeclarations()
    return a


class BusEndpointTC(unittest.TestCase):

    def test_HTypeFromIntfMap_Struct(self):
        DATA_WIDTH = 32

        t = HTypeFromIntfMap(
            IntfMap([
                    mk_regCntr("a", DATA_WIDTH),
                    mk_regCntr("b", DATA_WIDTH),
                    mk_sig("c", DATA_WIDTH),
                    mk_vldSynced("d", DATA_WIDTH),
            ]))

        _t = Bits(DATA_WIDTH)
        self.assertEqual(t, HStruct(
                (_t, "a"),
                (_t, "b"),
                (_t, "c"),
                (_t, "d"),
            ))

    def test_HTypeFromIntfMap_Padding(self):
        DATA_WIDTH = 32

        t = HTypeFromIntfMap(
            IntfMap([
                mk_regCntr("a", DATA_WIDTH),
                mk_regCntr("b", DATA_WIDTH),
                mk_sig("c", DATA_WIDTH),
                (Bits(4 * DATA_WIDTH), None),
                mk_vldSynced("d", DATA_WIDTH),
            ]))
        _t = Bits(DATA_WIDTH)
        t2 = HStruct(
                (_t, "a"),
                (_t, "b"),
                (_t, "c"),
                (Bits(4 * DATA_WIDTH), None),
                (_t, "d"),
            )

        self.assertEqual(t, t2)

    def test_HTypeFromIntfMap_Array(self):
        DATA_WIDTH = 32

        t = HTypeFromIntfMap(
            IntfMap([
                mk_regCntr("a", DATA_WIDTH),
                (Bits(4 * DATA_WIDTH), None),
                ([mk_vldSynced("d", DATA_WIDTH) for _ in range(4)], "ds")
            ]))

        _t = Bits(DATA_WIDTH)
        t2 = HStruct(
                (_t, "a"),
                (Bits(4 * DATA_WIDTH), None),
                (_t[4], "ds", HStructFieldMeta(split=True)),
            )
        self.assertEqual(t, t2)

    def test_HTypeFromIntfMap_ArrayOfStructs(self):
        DATA_WIDTH = 32

        t = HTypeFromIntfMap(
            IntfMap([
                mk_regCntr("a", DATA_WIDTH),
                (Bits(4 * DATA_WIDTH), None),
                ([IntfMap([
                    mk_vldSynced("c", DATA_WIDTH),
                    mk_vldSynced("d", DATA_WIDTH)
                ]) for _ in range(4)], "ds")
            ]))

        _t = Bits(DATA_WIDTH)
        _t2 = HStruct(
                (_t, "c"),
                (_t, "d")
            )
        t2 = HStruct(
                (_t, "a"),
                (Bits(4 * DATA_WIDTH), None),
                (_t2[4], "ds", HStructFieldMeta(split=True)),
            )

        self.assertEqual(t, t2)

    def test_HTypeFromIntfMap_ArrayOfStructsOfStructs(self):
        DATA_WIDTH = 32
        m = IntfMap([
                mk_regCntr("a", DATA_WIDTH),
                (Bits(4 * DATA_WIDTH), None),
                ([IntfMap([
                    (IntfMap([
                       mk_vldSynced("c", DATA_WIDTH),
                       mk_vldSynced("d", DATA_WIDTH)
                    ]), "nested")
                ]) for _ in range(4)], "ds")
            ])

        t = HTypeFromIntfMap(m)

        _t = Bits(DATA_WIDTH)
        _t2 = HStruct(
            (HStruct((_t, "c"),
                     (_t, "d")), "nested", HStructFieldMeta(split=True)))
        t2 = HStruct(
                (_t, "a"),
                (Bits(4 * DATA_WIDTH), None),
                (_t2[4], "ds", HStructFieldMeta(split=True)),
            )

        self.assertEqual(t, t2)

    def test_HTypeFromIntfMap_StructArray(self):
        DATA_WIDTH = 32

        t = HTypeFromIntfMap(
            IntfMap([
                mk_regCntr("a", DATA_WIDTH),
                (Bits(4 * DATA_WIDTH), None),
                ([
                    IntfMap([
                        mk_vldSynced("d", DATA_WIDTH),
                        mk_sig("e", DATA_WIDTH),
                        (Bits(DATA_WIDTH * 2), None),
                        mk_sig("f", DATA_WIDTH),
                    ]) for _ in range(4)], "ds")
            ]))

        _t = Bits(DATA_WIDTH)
        expected_t = HStruct(
            (_t, "a"),
            (Bits(4 * DATA_WIDTH), None),
            (HStruct(
                (_t, "d"),
                (_t, "e"),
                (Bits(2 * DATA_WIDTH), None),
                (_t, "f"),
                )[4], "ds", HStructFieldMeta(split=True)),
        )
        self.assertEqual(t, expected_t)

    def test_HTypeFromIntfMap_wrongArray(self):
        DATA_WIDTH = 32
        with self.assertRaises(AssertionError):
            HTypeFromIntfMap(
                IntfMap([
                    ([mk_sig("e", DATA_WIDTH),
                      mk_sig("e", 2 * DATA_WIDTH),
                      ], "ds")
                ]))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(BusEndpointTC('test_HTypeFromIntfMap_ArrayOfStructsOfStructs'))
    suite.addTest(unittest.makeSuite(BusEndpointTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
