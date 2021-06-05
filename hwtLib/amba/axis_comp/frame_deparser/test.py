#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import chain
from math import inf
import unittest

from hwt.hdl.constants import Time
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis import axis_send_bytes, axis_recieve_bytes
from hwtLib.amba.axis_comp.frame_deparser import AxiS_frameDeparser
from hwtLib.amba.axis_comp.frame_deparser.test_types import s1field, \
    s1field_composit0, s3field, s2Pading, unionOfStructs, unionSimple, \
    structStream64, structStream64before, structStream64after, struct2xStream64, \
    structStreamAndFooter, struct2xStream8, unionDifferentMask, \
    struct2xStream8_0B
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer
from pyMathBitPrecise.bit_utils import mask


class AxiS_frameDeparser_TC(SimTestCase):

    def instantiate(self, structT,
                    DATA_WIDTH=64,
                    maxFrameLen=inf,
                    maxPaddingWords=inf,
                    trimPaddingWordsOnStart=False,
                    trimPaddingWordsOnEnd=False,
                    randomized=True,
                    use_strb=False,
                    use_keep=True):
        if maxFrameLen is not inf\
                or maxPaddingWords is not inf\
                or trimPaddingWordsOnStart is not False\
                or trimPaddingWordsOnEnd is not False:
            tmpl = TransTmpl(structT)
            frames = list(FrameTmpl.framesFromTransTmpl(
                tmpl,
                DATA_WIDTH,
                maxFrameLen=maxFrameLen,
                maxPaddingWords=maxPaddingWords,
                trimPaddingWordsOnStart=trimPaddingWordsOnStart,
                trimPaddingWordsOnEnd=trimPaddingWordsOnEnd))
        else:
            tmpl = None
            frames = None

        u = self.u = AxiS_frameDeparser(structT, tmpl, frames)
        u.DATA_WIDTH = self.DATA_WIDTH = DATA_WIDTH
        u.USE_STRB = use_strb
        u.USE_KEEP = use_keep
        self.m = mask(self.DATA_WIDTH // 8)

        self.compileSimAndStart(self.u)
        if randomized:
            self.randomize(u.dataOut)
            for intf in u.dataIn._fieldsToInterfaces.values():
                self.randomize(intf)

    def formatStream(self, data):
        strb = self.m
        return [(d, strb, last)
                for last, d in iter_with_last(data)]

    def test_nop1Field(self, randomized=False):
        self.instantiate(s1field, randomized=randomized)
        u = self.u
        t = 100
        if randomized:
            t *= 2

        self.runSim(t * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)

    def test_1Field(self, randomized=False):
        self.instantiate(s1field, randomized=randomized)
        u = self.u
        MAGIC = 468
        u.dataIn.item0._ag.data.append(MAGIC)

        t = 100
        if randomized:
            t *= 2

        self.runSim(t * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, self.m, 1)])

    def test_1Field_halfvalid(self, randomized=False):
        self.instantiate(s1field, DATA_WIDTH=128,
                                   randomized=randomized)
        u = self.u
        MAGIC = 3
        u.dataIn.item0._ag.data.append(MAGIC)

        t = 100
        if randomized:
            t *= 2

        self.runSim(t * Time.ns)
        offset, f = axis_recieve_bytes(u.dataOut)
        self.assertEqual(offset, 0)
        self.assertSequenceEqual(f, [MAGIC, 0, 0, 0,
                                     0, 0, 0, 0])

    def test_1Field_composit0(self, randomized=False):
        self.instantiate(s1field_composit0, randomized=randomized)
        u = self.u
        MAGIC = 468
        u.dataIn.item0._ag.data.append(MAGIC)
        u.dataIn.item1._ag.data.append(MAGIC + 1)

        t = 100
        if randomized:
            t *= 2

        self.runSim(t * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(((MAGIC + 1) << 32) | MAGIC, self.m, 1)])

    def test_3Fields(self, randomized=False):
        self.instantiate(s3field, randomized=randomized)
        u = self.u
        MAGIC = 468
        u.dataIn.item0._ag.data.append(MAGIC)
        u.dataIn.item1._ag.data.append(MAGIC + 1)
        u.dataIn.item2._ag.data.append(MAGIC + 2)
        t = 200
        if randomized:
            t *= 3
        self.runSim(t * Time.ns)

        m = self.m
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
        u = self.u = AxiS_frameDeparser(s3field)
        u.USE_STRB = u.USE_KEEP = True
        u.DATA_WIDTH = self.DATA_WIDTH = 64
        m = mask(self.DATA_WIDTH // 8)

        self.compileSimAndStart(self.u)

        def enDataOut():
            u.dataOut._ag.enable = False
            yield Timer(50 * Time.ns)
            u.dataOut._ag.enable = True

        self.procs.append(enDataOut())

        MAGIC = 468
        u.dataIn.item0._ag.data.append(MAGIC)
        u.dataIn.item1._ag.data.append(MAGIC + 1)
        u.dataIn.item2._ag.data.append(MAGIC + 2)

        t = 200
        self.runSim(t * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, m, 0),
                                     (MAGIC + 1, m, m, 0),
                                     (MAGIC + 2, m, m, 1),
                                     ])

    def test_s2Pading_normal(self):
        u = self.u = AxiS_frameDeparser(s2Pading)
        self.DATA_WIDTH = 64
        u.USE_STRB = u.USE_KEEP = True
        u.DATA_WIDTH = self.DATA_WIDTH
        m = mask(self.DATA_WIDTH // 8)
        self.compileSimAndStart(self.u)

        def enDataOut():
            u.dataOut._ag.enable = False
            yield Timer(50 * Time.ns)
            u.dataOut._ag.enable = True

        self.procs.append(enDataOut())

        MAGIC = 468
        u.dataIn.item0_0._ag.data.append(MAGIC)
        u.dataIn.item0_1._ag.data.append(MAGIC + 1)
        u.dataIn.item1_0._ag.data.append(MAGIC + 2)
        u.dataIn.item1_1._ag.data.append(MAGIC + 3)

        t = 200
        self.runSim(t * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, m, 0),
                                     (MAGIC + 1, m, m, 0),
                                     (None, 0, m, 0),
                                     (MAGIC + 2, m, m, 0),
                                     (MAGIC + 3, m, m, 0),
                                     (None, 0, m, 1),
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
        u = self.u = AxiS_frameDeparser(structT,
                                     tmpl, frames)
        u.DATA_WIDTH = self.DATA_WIDTH
        m = mask(self.DATA_WIDTH // 8)
        self.compileSimAndStart(self.u)

        def enDataOut():
            u.dataOut._ag.enable = False
            yield Timer(50 * Time.ns)
            u.dataOut._ag.enable = True

        self.procs.append(enDataOut())

        MAGIC = 468
        u.dataIn.item0_0._ag.data.append(MAGIC)
        u.dataIn.item0_1._ag.data.append(MAGIC + 1)
        u.dataIn.item1_0._ag.data.append(MAGIC + 2)
        u.dataIn.item1_1._ag.data.append(MAGIC + 3)

        t = 200
        self.runSim(t * Time.ns)

        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC, m, 0),
                                     (MAGIC + 1, m, 1),
                                     (MAGIC + 2, m, 0),
                                     (MAGIC + 3, m, 1),
                                     ])

    def test_unionOfStructs_nop(self, randomized=False):
        self.instantiate(unionOfStructs, randomized=randomized)
        u = self.u
        t = 60
        if randomized:
            t *= 3
        self.runSim(t * Time.ns)

        self.assertEmpty(u.dataOut._ag.data)

    def test_r_unionOfStructs_nop(self):
        self.test_unionOfStructs_nop(randomized=True)

    def test_unionOfStructs_frameA(self, randomized=False):
        self.instantiate(unionOfStructs, randomized=randomized)
        u = self.u
        MAGIC = 498
        t = 120
        if randomized:
            t *= 8

        u.dataIn.frameA.itemA0._ag.data.extend([MAGIC + 1, MAGIC + 3])
        u.dataIn.frameA.itemA1._ag.data.extend([MAGIC + 2, MAGIC + 4])
        u.dataIn._select._ag.data.extend([0, 0])

        self.runSim(t * Time.ns)

        m = self.m
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC + 1, m, 0),
                                     (MAGIC + 2, m, 1),
                                     (MAGIC + 3, m, 0),
                                     (MAGIC + 4, m, 1),
                                     ])

    def test_r_unionOfStructs_frameA(self):
        self.test_unionOfStructs_frameA(randomized=True)

    def test_unionOfStructs_simple(self, randomized=False):
        self.instantiate(unionSimple,
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

        m = self.m
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC + 1, m, 1),
                                     (MAGIC + 2, m, 1),
                                     (MAGIC + 3, m, 1),
                                     ])

    def test_r_unionOfStructs_simple(self):
        self.test_unionOfStructs_simple(randomized=True)

    def test_stream64(self, randomized=False):
        self.instantiate(structStream64,
                         DATA_WIDTH=64,
                         randomized=randomized)
        u = self.u
        MAGIC = 498
        t = 100
        if randomized:
            t *= 3

        u.dataIn.streamIn._ag.data.extend(
            self.formatStream([MAGIC + 1, MAGIC + 2, MAGIC + 3]) +
            self.formatStream([MAGIC + 4, MAGIC + 5, MAGIC + 6])
        )

        self.runSim(t * Time.ns)

        m = self.m
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC + 1, m, 0),
                                     (MAGIC + 2, m, 0),
                                     (MAGIC + 3, m, 1),
                                     (MAGIC + 4, m, 0),
                                     (MAGIC + 5, m, 0),
                                     (MAGIC + 6, m, 1),
                                     ])

    def test_r_stream64(self):
        self.test_stream64(randomized=True)

    def test_structStream64before(self, randomized=False):
        self.instantiate(structStream64before,
                         DATA_WIDTH=64,
                         randomized=randomized)
        u = self.u
        MAGIC = 498
        t = 120
        if randomized:
            t *= 3

        u.dataIn.streamIn._ag.data.extend(
            self.formatStream([MAGIC + 1, MAGIC + 2, MAGIC + 3]) +
            self.formatStream([MAGIC + 5, MAGIC + 6, MAGIC + 7])
        )
        u.dataIn.item0._ag.data.extend([MAGIC + 4, MAGIC + 8])

        self.runSim(t * Time.ns)

        m = self.m
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [(MAGIC + 1, m, 0),
                                     (MAGIC + 2, m, 0),
                                     (MAGIC + 3, m, 0),
                                     (MAGIC + 4, m, 1),
                                     (MAGIC + 5, m, 0),
                                     (MAGIC + 6, m, 0),
                                     (MAGIC + 7, m, 0),
                                     (MAGIC + 8, m, 1),
                                     ])

    def test_r_structStream64before(self):
        self.test_structStream64before(randomized=True)

    def test_structStream64after(self, randomized=False):
        self.instantiate(structStream64after,
                         DATA_WIDTH=64,
                         randomized=randomized)
        u = self.u
        MAGIC = 498
        t = 100
        if randomized:
            t *= 3

        u.dataIn.streamIn._ag.data.extend(
            self.formatStream([MAGIC + 1, MAGIC + 2, MAGIC + 3]) +
            self.formatStream([MAGIC + 5, MAGIC + 6, MAGIC + 7])
        )
        u.dataIn.item0._ag.data.extend([MAGIC + 4, MAGIC + 8])

        self.runSim(t * Time.ns)

        m = self.m
        self.assertValSequenceEqual(u.dataOut._ag.data,
                                    [
                                     (MAGIC + 4, m, 0),
                                     (MAGIC + 1, m, 0),
                                     (MAGIC + 2, m, 0),
                                     (MAGIC + 3, m, 1),
                                     (MAGIC + 8, m, 0),
                                     (MAGIC + 5, m, 0),
                                     (MAGIC + 6, m, 0),
                                     (MAGIC + 7, m, 1),
                                     ])

    def test_r_structStream64after(self):
        self.test_structStream64after(randomized=True)

    def test_struct2xStream64(self, N=5, randomized=False):
        self.instantiate(struct2xStream64,
                         DATA_WIDTH=64,
                         randomized=randomized)
        u = self.u
        MAGIC = 400
        t = 10 + (2 * N * 3)
        if randomized:
            t *= 3

        for i in range(N):
            o = MAGIC + i * 6
            u.dataIn.streamIn0._ag.data.extend(
                self.formatStream([o + 1, o + 2, o + 3])
            )
            u.dataIn.streamIn1._ag.data.extend(
                self.formatStream([o + 4, o + 5, o + 6])
            )

        self.runSim(t * CLK_PERIOD)

        m = self.m
        ref = [
            (MAGIC + i, m, int(i % 6 == 0))
            for i in range(1, N * 6 + 1)
        ]
        self.assertValSequenceEqual(
            u.dataOut._ag.data, ref)

    def test_r_struct2xStream64(self):
        self.test_struct2xStream64(randomized=True)

    def test_footer(self, randomized=False):
        self.instantiate(structStreamAndFooter,
                         DATA_WIDTH=16,
                         randomized=randomized)
        u = self.u

        def mk_footer(d):
            v = 0
            for i in range(4):
                v |= (d + i) << (8 * i)
            return v

        axis_send_bytes(u.dataIn.data, [1, 2])
        u.dataIn.footer._ag.data.append(mk_footer(3))
        axis_send_bytes(u.dataIn.data, [8, 9, 10, 11])
        u.dataIn.footer._ag.data.append(mk_footer(12))
        t = 170
        if randomized:
            t *= 3
        self.runSim(t * Time.ns)
        offset, f = axis_recieve_bytes(u.dataOut)
        self.assertEqual(offset, 0)
        self.assertValSequenceEqual(f, list(range(1, 3 + 4)))
        offset, f = axis_recieve_bytes(u.dataOut)
        self.assertEqual(offset, 0)
        self.assertValSequenceEqual(f, list(range(8, 12 + 4)))
        self.assertEmpty(u.dataOut._ag.data)

    def test_r_footer(self):
        self.test_footer(randomized=True)

    def test_struct2xStream8(self, randomized=False,
                             T=struct2xStream8,
                             sizes=[(2, 2), (1, 2),
                                    (1, 3), (2, 1),
                                    (2, 2)]):
        self.instantiate(T,
                         DATA_WIDTH=16,
                         randomized=randomized)
        # for i, stg in enumerate(self.u.frame_join.state_trans_table.state_trans):
        #     print(f"{i:d}:")
        #     for stt in stg:
        #         print(stt)

        u = self.u
        MAGIC = 0  # 13
        t = 10 + (2 * sum(sum(x) for x in sizes) * 3)
        if randomized:
            t *= 3

        ref = []
        for i, size in enumerate(sizes):
            o = MAGIC + i * 6 + 1
            d0 = [o + i for i in range(size[0])]
            axis_send_bytes(u.dataIn.streamIn0, d0)
            d1 = [o + i + size[0] for i in range(size[1])]
            axis_send_bytes(u.dataIn.streamIn1, d1)
            ref.append(list(chain(d0, d1)))
        self.runSim(t * CLK_PERIOD)
        for i, ref_f in enumerate(ref):
            f_offset, f = axis_recieve_bytes(u.dataOut)
            self.assertValEqual(f_offset, 0)
            self.assertValSequenceEqual(f, ref_f, i)

    def test_r_struct2xStream8(self):
        self.test_struct2xStream8(randomized=True)

    def test_struct2xStream8_0B(self, randomized=False,
                                T=struct2xStream8_0B,
                             sizes=[
                                 (3, 0), (0, 0),
                                 #(2, 2), (0, 2), (1, 2), (0, 1),
                                 #(1, 3), (1, 0), (2, 1), (2, 0),
                                 #(2, 2), (3, 0), (0, 0), (1, 1)
                                 ]):
        self.test_struct2xStream8(randomized=randomized, T=T, sizes=sizes)

    def test_r_struct2xStream8_0B(self):
        self.test_struct2xStream8_0B(randomized=True)

    def test_unionDifferentMask(self, N=10, randomized=False):
        self.instantiate(unionDifferentMask,
                         DATA_WIDTH=16,
                         randomized=randomized,
                         use_keep=False,
                         use_strb=True)
        u = self.u
        MAGIC = 0  # 13
        t = 10 + N
        if randomized:
            t *= 3
        ref = []
        for i in range(N):
            i += MAGIC
            if self._rand.getrandbits(1):
                d = (1, [i, ])
                u.dataIn.u1.data._ag.data.append(i)
                u.dataIn._select._ag.data.append(1)
            else:
                d = (0, [i, ])
                u.dataIn.u0.data._ag.data.append(i)
                u.dataIn._select._ag.data.append(0)
            ref.append(d)
        self.runSim(t * CLK_PERIOD)
        for i, ref_f in enumerate(ref):
            ref_offset, ref_data = ref_f
            f_offset, f = axis_recieve_bytes(u.dataOut)
            self.assertEqual(f_offset, ref_offset)
            self.assertValSequenceEqual(f, ref_data)

    def test_unionDifferentMask_randomized(self):
        self.test_unionDifferentMask(randomized=True)


if __name__ == "__main__":

    suite = unittest.TestSuite()
    # suite.addTest(AxiS_frameDeparser_TC('test_struct2xStream8_0B'))
    suite.addTest(unittest.makeSuite(AxiS_frameDeparser_TC))
    runner = unittest.TextTestRunner(verbosity=3)

    runner.run(suite)
