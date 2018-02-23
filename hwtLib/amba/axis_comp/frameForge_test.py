#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import inf
import unittest

from hwt.bitmask import mask
from hwt.hdl.constants import Time
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.union import HUnion
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.frameForge import AxiS_frameForge
from hwtLib.types.ctypes import uint64_t, uint32_t, int32_t


s1field = HStruct(
    (uint64_t, "item0")
    )

s3field = HStruct(
    (uint64_t, "item0"),
    (uint64_t, "item1"),
    (uint64_t, "item2")
    )

s2Pading = HStruct(
    (uint64_t, "item0_0"),
    (uint64_t, "item0_1"),
    (uint64_t, None),
    (uint64_t, "item1_0"),
    (uint64_t, "item1_1"),
    (uint64_t, None),
    )

s1field_composit0 = HStruct(
    (uint32_t, "item0"), (uint32_t, "item1"),
    )

unionOfStructs = HUnion(
        (HStruct(
            (uint64_t, "itemA0"),
            (uint64_t, "itemA1")
            ), "frameA"),
        (HStruct(
            (uint32_t, "itemB0"),
            (uint32_t, "itemB1"),
            (uint32_t, "itemB2"),
            (uint32_t, "itemB3")
            ), "frameB")
        )

unionSimple = HUnion(
        (uint32_t, "a"),
        (int32_t, "b")
        )


class AxiS_frameForge_TC(SimTestCase):
    def instantiateFrameForge(self, structT,
                              DATA_WIDTH=64,
                              maxFrameLen=inf,
                              maxPaddingWords=inf,
                              trimPaddingWordsOnStart=False,
                              trimPaddingWordsOnEnd=False,
                              randomized=True):
        tmpl = TransTmpl(structT)
        frames = list(FrameTmpl.framesFromTransTmpl(
                                     tmpl,
                                     DATA_WIDTH,
                                     maxFrameLen=maxFrameLen,
                                     maxPaddingWords=maxPaddingWords,
                                     trimPaddingWordsOnStart=trimPaddingWordsOnStart,
                                     trimPaddingWordsOnEnd=trimPaddingWordsOnEnd))
        u = self.u = AxiS_frameForge(AxiStream, structT,
                                     tmpl, frames)
        self.DATA_WIDTH = DATA_WIDTH
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u)
        if randomized:
            self.randomize(u.dataOut)
            for intf in u.dataIn._fieldsToInterfaces.values():
                self.randomize(intf)

    def test_nop1Field(self, randomized=False):
        self.instantiateFrameForge(s1field, randomized=randomized)
        u = self.u
        t = 100
        if randomized:
            t *= 2

        self.runSim(t * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)

    def test_1Field(self, randomized=False):
        self.instantiateFrameForge(s1field, randomized=randomized)
        u = self.u
        MAGIC = 468
        u.dataIn.item0._ag.data.append(MAGIC)

        t = 100
        if randomized:
            t *= 2

        self.runSim(t * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, mask(self.DATA_WIDTH // 8), 1)])

    def test_1Field_composit0(self, randomized=False):
        self.instantiateFrameForge(s1field_composit0, randomized=randomized)
        u = self.u
        MAGIC = 468
        u.dataIn.item0._ag.data.append(MAGIC)
        u.dataIn.item1._ag.data.append(MAGIC + 1)

        t = 100
        if randomized:
            t *= 2

        self.runSim(t * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(((MAGIC + 1) << 32) | MAGIC, mask(self.DATA_WIDTH // 8), 1)])

    def test_3Fields(self, randomized=False):
        self.instantiateFrameForge(s3field, randomized=randomized)
        u = self.u
        MAGIC = 468
        u.dataIn.item0._ag.data.append(MAGIC)
        u.dataIn.item1._ag.data.append(MAGIC + 1)
        u.dataIn.item2._ag.data.append(MAGIC + 2)
        t = 200
        if randomized:
            t *= 3
        self.runSim(t * Time.ns)

        m = mask(self.DATA_WIDTH // 8)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, 0),
                                     (MAGIC + 1, m, 0),
                                     (MAGIC + 2, m, 1),
                                     ])

    def test_r_nop1Field(self):
        self.test_nop1Field(randomized=True)

    def test_r_1Field(self):
        self.test_1Field(randomized=True)

    def test_r_3Fields(self):
        self.test_3Fields(randomized=True)

    def test_r_1Field_composit0(self):
        self.test_1Field_composit0(randomized=True)

    def test_3Fields_outOccupiedAtStart(self):
        u = self.u = AxiS_frameForge(AxiStream, s3field)
        self.DATA_WIDTH = 64
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u)

        def enDataOut(s):
            u.dataOut._ag.enable = False
            yield s.wait(50 * Time.ns)
            u.dataOut._ag.enable = True
        self.procs.append(enDataOut)

        MAGIC = 468
        u.dataIn.item0._ag.data.append(MAGIC)
        u.dataIn.item1._ag.data.append(MAGIC + 1)
        u.dataIn.item2._ag.data.append(MAGIC + 2)

        t = 200
        self.runSim(t * Time.ns)

        m = mask(self.DATA_WIDTH // 8)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, 0),
                                     (MAGIC + 1, m, 0),
                                     (MAGIC + 2, m, 1),
                                     ])

    def test_s2Pading_normal(self):
        u = self.u = AxiS_frameForge(AxiStream, s2Pading)
        self.DATA_WIDTH = 64
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u)

        def enDataOut(s):
            u.dataOut._ag.enable = False
            yield s.wait(50 * Time.ns)
            u.dataOut._ag.enable = True
        self.procs.append(enDataOut)

        MAGIC = 468
        u.dataIn.item0_0._ag.data.append(MAGIC)
        u.dataIn.item0_1._ag.data.append(MAGIC + 1)
        u.dataIn.item1_0._ag.data.append(MAGIC + 2)
        u.dataIn.item1_1._ag.data.append(MAGIC + 3)

        t = 200
        self.runSim(t * Time.ns)

        m = mask(self.DATA_WIDTH // 8)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, 0),
                                     (MAGIC + 1, m, 0),
                                     (None, m, 0),
                                     (MAGIC + 2, m, 0),
                                     (MAGIC + 3, m, 0),
                                     (None, m, 1),
                                     ])

    def test_s2Pading_spliting(self):
        structT = s2Pading
        self.DATA_WIDTH = 64
        tmpl = TransTmpl(structT)
        frames = list(FrameTmpl.framesFromTransTmpl(
                                     tmpl,
                                     self.DATA_WIDTH,
                                     maxPaddingWords=0,
                                     trimPaddingWordsOnStart=True,
                                     trimPaddingWordsOnEnd=True))
        u = self.u = AxiS_frameForge(AxiStream, structT,
                                     tmpl, frames)
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u)

        def enDataOut(s):
            u.dataOut._ag.enable = False
            yield s.wait(50 * Time.ns)
            u.dataOut._ag.enable = True
        self.procs.append(enDataOut)

        MAGIC = 468
        u.dataIn.item0_0._ag.data.append(MAGIC)
        u.dataIn.item0_1._ag.data.append(MAGIC + 1)
        u.dataIn.item1_0._ag.data.append(MAGIC + 2)
        u.dataIn.item1_1._ag.data.append(MAGIC + 3)

        t = 200
        self.runSim(t * Time.ns)

        m = mask(self.DATA_WIDTH // 8)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, 0),
                                     (MAGIC + 1, m, 1),
                                     (MAGIC + 2, m, 0),
                                     (MAGIC + 3, m, 1),
                                     ])

    def test_unionOfStructs_nop(self, randomized=False):
        self.instantiateFrameForge(unionOfStructs, randomized=randomized)
        u = self.u
        t = 60
        if randomized:
            t *= 3
        self.runSim(t * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)

    def test_r_unionOfStructs_nop(self):
        self.test_unionOfStructs_nop(randomized=True)

    def test_unionOfStructs_frameA(self, randomized=False):
        self.instantiateFrameForge(unionOfStructs, randomized=randomized)
        u = self.u
        MAGIC = 498
        t = 120
        if randomized:
            t *= 8

        u.dataIn.frameA.itemA0._ag.data.extend([MAGIC + 1, MAGIC + 3])
        u.dataIn.frameA.itemA1._ag.data.extend([MAGIC + 2, MAGIC + 4])
        u.dataIn._select._ag.data.extend([0, 0])

        self.runSim(t * Time.ns)

        m = mask(self.DATA_WIDTH // 8)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC + 1, m, 0),
                                     (MAGIC + 2, m, 1),
                                     (MAGIC + 3, m, 0),
                                     (MAGIC + 4, m, 1),
                                     ])

    def test_r_unionOfStructs_frameA(self):
        self.test_unionOfStructs_frameA(randomized=True)

    def test_unionOfStructs_simple(self, randomized=False):
        self.instantiateFrameForge(unionSimple,
                                   DATA_WIDTH=32,
                                   randomized=randomized)
        u = self.u
        MAGIC = 498
        t = 50
        if randomized:
            t *= 6

        u.dataIn.a._ag.data.extend([MAGIC + 1, MAGIC + 3])
        u.dataIn.b._ag.data.extend([MAGIC + 2])
        u.dataIn._select._ag.data.extend([0, 1, 0])

        self.runSim(t * Time.ns)

        m = mask(self.DATA_WIDTH // 8)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC + 1, m, 1),
                                     (MAGIC + 2, m, 1),
                                     (MAGIC + 3, m, 1),
                                     ])

    def test_r_unionOfStructs_simple(self):
        self.test_unionOfStructs_simple(randomized=True)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_frameForge_TC('test_unionOfStructs_simple'))
    suite.addTest(unittest.makeSuite(AxiS_frameForge_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
