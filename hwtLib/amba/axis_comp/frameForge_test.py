#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.bitmask import mask
from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.types.struct import HStruct
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.frameForge import AxiS_frameForge
from hwtLib.types.ctypes import uint64_t, uint32_t
from math import inf
from hwt.synthesizer.shortcuts import toRtl
from hwt.hdlObjects.transTmpl import TransTmpl
from hwt.hdlObjects.frameTemplate import FrameTemplate


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


class AxiS_frameForge_TC(SimTestCase):
    def instantiateFrameForge(self, structT,
                              DATA_WIDTH=64,
                              maxFrameLen=inf,
                              maxPaddingWords=inf,
                              trimPaddingWordsOnStart=False,
                              trimPaddingWordsOnEnd=False,
                              randomized=True):
        tmpl = TransTmpl(structT)
        frames = list(FrameTemplate.framesFromTransTmpl(
                                     tmpl,
                                     DATA_WIDTH,
                                     maxFrameLen=maxFrameLen,
                                     maxPaddingWords=maxPaddingWords,
                                     trimPaddingWordsOnStart=trimPaddingWordsOnStart,
                                     trimPaddingWordsOnEnd=trimPaddingWordsOnEnd))
        u = self.u = AxiS_frameForge(AxiStream, structT,
                                     tmpl, frames)
        self.DATA_WIDTH = 64
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

        self.doSim(t * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)

    def test_1Field(self, randomized=False):
        self.instantiateFrameForge(s1field, randomized=randomized)
        u = self.u
        MAGIC = 468
        u.dataIn.item0._ag.data.append(MAGIC)

        t = 100
        if randomized:
            t *= 2

        self.doSim(t * Time.ns)

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

        self.doSim(t * Time.ns)

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
        self.doSim(t * Time.ns)

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

    def test_r_test_1Field_composit0(self):
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
        self.doSim(t * Time.ns)

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
        self.doSim(t * Time.ns)

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
        frames = list(FrameTemplate.framesFromTransTmpl(
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
        self.doSim(t * Time.ns)

        m = mask(self.DATA_WIDTH // 8)
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, 0),
                                     (MAGIC + 1, m, 1),
                                     (MAGIC + 2, m, 0),
                                     (MAGIC + 3, m, 1),
                                     ])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_resizer_downscale_TC('test_noPass'))
    suite.addTest(unittest.makeSuite(AxiS_frameForge_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
