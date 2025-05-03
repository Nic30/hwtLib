#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import chain
from math import inf
import unittest

from hwt.constants import Time
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4s import Axi4StreamFrameUtils, axi4s_send_bytes,\
    axi4s_receive_bytes
from hwtLib.amba.axis_comp.frame_deparser import Axi4S_frameDeparser
from hwtLib.amba.axis_comp.frame_deparser.test_types import s1field, \
    s1field_composit0, s3field, s2Pading, unionOfStructs, unionSimple, \
    structStream64, structStream64before, structStream64after, struct2xStream64, \
    structStreamAndFooter, struct2xStream8, unionDifferentMask, \
    struct2xStream8_0B
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer
from pyMathBitPrecise.bit_utils import mask


class Axi4S_frameDeparser_TC(SimTestCase):

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

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

        dut = self.dut = Axi4S_frameDeparser(structT, tmpl, frames)
        dut.DATA_WIDTH = self.DATA_WIDTH = DATA_WIDTH
        dut.USE_STRB = use_strb
        dut.USE_KEEP = use_keep
        self.m = mask(self.DATA_WIDTH // 8)

        self.compileSimAndStart(self.dut)
        if randomized:
            self.randomize(dut.dataOut)
            for intf in dut.dataIn._fieldsToHwIOs.values():
                self.randomize(intf)

    def formatStream(self, data):
        strb = self.m
        return [(d, strb, last)
                for last, d in iter_with_last(data)]

    def test_nop1Field(self, randomized=False):
        self.instantiate(s1field, randomized=randomized)
        dut = self.dut
        t = 100
        if randomized:
            t *= 2

        self.runSim(t * Time.ns)

        self.assertEmpty(dut.dataOut._ag.data)

    def test_1Field(self, randomized=False):
        self.instantiate(s1field, randomized=randomized)
        dut = self.dut
        MAGIC = 468
        dut.dataIn.item0._ag.data.append(MAGIC)

        t = 100
        if randomized:
            t *= 2

        self.runSim(t * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    [(MAGIC, self.m, 1)])

    def test_1Field_halfvalid(self, randomized=False):
        self.instantiate(s1field, DATA_WIDTH=128, randomized=randomized)
        dut = self.dut
        MAGIC = 3
        dut.dataIn.item0._ag.data.append(MAGIC)

        t = 100
        if randomized:
            t *= 2

        self.runSim(t * Time.ns)

        fu = Axi4StreamFrameUtils.from_HwIO(dut.dataOut)
        offset, f = fu.receive_bytes(dut.dataOut._ag.data)
        self.assertEqual(offset, 0)
        self.assertSequenceEqual(f, [MAGIC, 0, 0, 0,
                                     0, 0, 0, 0])

    def test_1Field_composit0(self, randomized=False):
        self.instantiate(s1field_composit0, randomized=randomized)
        dut = self.dut
        MAGIC = 468
        dut.dataIn.item0._ag.data.append(MAGIC)
        dut.dataIn.item1._ag.data.append(MAGIC + 1)

        t = 100
        if randomized:
            t *= 2

        self.runSim(t * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    [(((MAGIC + 1) << 32) | MAGIC, self.m, 1)])

    def test_3Fields(self, randomized=False):
        self.instantiate(s3field, randomized=randomized)
        dut = self.dut
        MAGIC = 468
        dut.dataIn.item0._ag.data.append(MAGIC)
        dut.dataIn.item1._ag.data.append(MAGIC + 1)
        dut.dataIn.item2._ag.data.append(MAGIC + 2)
        t = 200
        if randomized:
            t *= 3
        self.runSim(t * Time.ns)

        m = self.m
        self.assertValSequenceEqual(dut.dataOut._ag.data,
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
        dut = self.dut = Axi4S_frameDeparser(s3field)
        dut.USE_STRB = dut.USE_KEEP = True
        dut.DATA_WIDTH = self.DATA_WIDTH = 64
        m = mask(self.DATA_WIDTH // 8)

        self.compileSimAndStart(self.dut)

        def enDataOut():
            dut.dataOut._ag.enable = False
            yield Timer(50 * Time.ns)
            dut.dataOut._ag.enable = True

        self.procs.append(enDataOut())

        MAGIC = 468
        dut.dataIn.item0._ag.data.append(MAGIC)
        dut.dataIn.item1._ag.data.append(MAGIC + 1)
        dut.dataIn.item2._ag.data.append(MAGIC + 2)

        t = 200
        self.runSim(t * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    [(MAGIC, m, m, 0),
                                     (MAGIC + 1, m, m, 0),
                                     (MAGIC + 2, m, m, 1),
                                     ])

    def test_s2Pading_normal(self):
        self.dut = dut = Axi4S_frameDeparser(s2Pading)
        self.DATA_WIDTH = 64
        dut.USE_STRB = dut.USE_KEEP = True
        dut.DATA_WIDTH = self.DATA_WIDTH
        m = mask(self.DATA_WIDTH // 8)
        self.compileSimAndStart(self.dut)

        def enDataOut():
            dut.dataOut._ag.enable = False
            yield Timer(50 * Time.ns)
            dut.dataOut._ag.enable = True

        self.procs.append(enDataOut())

        MAGIC = 468
        dut.dataIn.item0_0._ag.data.append(MAGIC)
        dut.dataIn.item0_1._ag.data.append(MAGIC + 1)
        dut.dataIn.item1_0._ag.data.append(MAGIC + 2)
        dut.dataIn.item1_1._ag.data.append(MAGIC + 3)

        t = 200
        self.runSim(t * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data,
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
        self.dut = dut = Axi4S_frameDeparser(structT,
                                     tmpl, frames)
        dut.DATA_WIDTH = self.DATA_WIDTH
        m = mask(self.DATA_WIDTH // 8)
        self.compileSimAndStart(self.dut)

        def enDataOut():
            dut.dataOut._ag.enable = False
            yield Timer(50 * Time.ns)
            dut.dataOut._ag.enable = True

        self.procs.append(enDataOut())

        MAGIC = 468
        dut.dataIn.item0_0._ag.data.append(MAGIC)
        dut.dataIn.item0_1._ag.data.append(MAGIC + 1)
        dut.dataIn.item1_0._ag.data.append(MAGIC + 2)
        dut.dataIn.item1_1._ag.data.append(MAGIC + 3)

        t = 200
        self.runSim(t * Time.ns)

        self.assertValSequenceEqual(dut.dataOut._ag.data,
                                    [(MAGIC, m, 0),
                                     (MAGIC + 1, m, 1),
                                     (MAGIC + 2, m, 0),
                                     (MAGIC + 3, m, 1),
                                     ])

    def test_unionOfStructs_nop(self, randomized=False):
        self.instantiate(unionOfStructs, randomized=randomized)
        dut = self.dut
        t = 60
        if randomized:
            t *= 3
        self.runSim(t * Time.ns)

        self.assertEmpty(dut.dataOut._ag.data)

    def test_r_unionOfStructs_nop(self):
        self.test_unionOfStructs_nop(randomized=True)

    def test_unionOfStructs_frameA(self, randomized=False):
        self.instantiate(unionOfStructs, randomized=randomized)
        dut = self.dut
        MAGIC = 498
        t = 120
        if randomized:
            t *= 8

        dut.dataIn.frameA.itemA0._ag.data.extend([MAGIC + 1, MAGIC + 3])
        dut.dataIn.frameA.itemA1._ag.data.extend([MAGIC + 2, MAGIC + 4])
        dut.dataIn._select._ag.data.extend([0, 0])

        self.runSim(t * Time.ns)

        m = self.m
        self.assertValSequenceEqual(dut.dataOut._ag.data,
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
        dut = self.dut
        MAGIC = 498
        t = 50
        if randomized:
            t *= 6

        dut.dataIn.a._ag.data.extend([MAGIC + 1, MAGIC + 3])
        dut.dataIn.b._ag.data.extend([MAGIC + 2])
        dut.dataIn._select._ag.data.extend([0, 1, 0])

        self.runSim(t * Time.ns)

        m = self.m
        self.assertValSequenceEqual(dut.dataOut._ag.data,
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
        dut = self.dut
        MAGIC = 498
        t = 100
        if randomized:
            t *= 3

        dut.dataIn.streamIn._ag.data.extend(
            self.formatStream([MAGIC + 1, MAGIC + 2, MAGIC + 3]) +
            self.formatStream([MAGIC + 4, MAGIC + 5, MAGIC + 6])
        )

        self.runSim(t * Time.ns)

        m = self.m
        self.assertValSequenceEqual(dut.dataOut._ag.data,
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
        dut = self.dut
        MAGIC = 498
        t = 120
        if randomized:
            t *= 3

        dut.dataIn.streamIn._ag.data.extend(
            self.formatStream([MAGIC + 1, MAGIC + 2, MAGIC + 3]) +
            self.formatStream([MAGIC + 5, MAGIC + 6, MAGIC + 7])
        )
        dut.dataIn.item0._ag.data.extend([MAGIC + 4, MAGIC + 8])

        self.runSim(t * Time.ns)

        m = self.m
        self.assertValSequenceEqual(dut.dataOut._ag.data,
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
        dut = self.dut
        MAGIC = 498
        t = 100
        if randomized:
            t *= 3

        dut.dataIn.streamIn._ag.data.extend(
            self.formatStream([MAGIC + 1, MAGIC + 2, MAGIC + 3]) +
            self.formatStream([MAGIC + 5, MAGIC + 6, MAGIC + 7])
        )
        dut.dataIn.item0._ag.data.extend([MAGIC + 4, MAGIC + 8])

        self.runSim(t * Time.ns)

        m = self.m
        self.assertValSequenceEqual(dut.dataOut._ag.data,
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
        dut = self.dut
        MAGIC = 400
        t = 10 + (2 * N * 3)
        if randomized:
            t *= 3

        for i in range(N):
            o = MAGIC + i * 6
            dut.dataIn.streamIn0._ag.data.extend(
                self.formatStream([o + 1, o + 2, o + 3])
            )
            dut.dataIn.streamIn1._ag.data.extend(
                self.formatStream([o + 4, o + 5, o + 6])
            )

        self.runSim(t * CLK_PERIOD)

        m = self.m
        ref = [
            (MAGIC + i, m, int(i % 6 == 0))
            for i in range(1, N * 6 + 1)
        ]
        self.assertValSequenceEqual(
            dut.dataOut._ag.data, ref)

    def test_r_struct2xStream64(self):
        self.test_struct2xStream64(randomized=True)

    def test_footer(self, randomized=False):
        self.instantiate(structStreamAndFooter,
                         DATA_WIDTH=16,
                         randomized=randomized)
        dut = self.dut

        def mk_footer(d):
            v = 0
            for i in range(4):
                v |= (d + i) << (8 * i)
            return v

        axi4s_send_bytes(dut.dataIn.data, [1, 2])
        dut.dataIn.footer._ag.data.append(mk_footer(3))
        axi4s_send_bytes(dut.dataIn.data, [8, 9, 10, 11])
        dut.dataIn.footer._ag.data.append(mk_footer(12))
        t = 170
        if randomized:
            t *= 3
        self.runSim(t * Time.ns)
        offset, f = axi4s_receive_bytes(dut.dataOut)
        self.assertEqual(offset, 0)
        self.assertValSequenceEqual(f, list(range(1, 3 + 4)))
        offset, f = axi4s_receive_bytes(dut.dataOut)
        self.assertEqual(offset, 0)
        self.assertValSequenceEqual(f, list(range(8, 12 + 4)))
        self.assertEmpty(dut.dataOut._ag.data)

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
        # for i, stg in enumerate(self.dut.frame_join.state_trans_table.state_trans):
        #     print(f"{i:d}:")
        #     for stt in stg:
        #         print(stt)

        dut = self.dut
        MAGIC = 0  # 13
        t = 10 + (2 * sum(sum(x) for x in sizes) * 3)
        if randomized:
            t *= 3

        ref = []
        for i, size in enumerate(sizes):
            o = MAGIC + i * 6 + 1
            d0 = [o + i for i in range(size[0])]
            axi4s_send_bytes(dut.dataIn.streamIn0, d0)
            d1 = [o + i + size[0] for i in range(size[1])]
            axi4s_send_bytes(dut.dataIn.streamIn1, d1)
            ref.append(list(chain(d0, d1)))
        self.runSim(t * CLK_PERIOD)
        for i, ref_f in enumerate(ref):
            f_offset, f = axi4s_receive_bytes(dut.dataOut)
            self.assertValEqual(f_offset, 0)
            self.assertValSequenceEqual(f, ref_f, i)

    def test_r_struct2xStream8(self):
        self.test_struct2xStream8(randomized=True)

    def test_struct2xStream8_0B(self, randomized=False,
                                T=struct2xStream8_0B,
                             sizes=[
                                 (3, 0), (0, 0),
                                 # (2, 2), (0, 2), (1, 2), (0, 1),
                                 # (1, 3), (1, 0), (2, 1), (2, 0),
                                 # (2, 2), (3, 0), (0, 0), (1, 1)
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
        dut = self.dut
        MAGIC = 0  # 13
        t = 10 + N
        if randomized:
            t *= 3
        ref = []
        for i in range(N):
            i += MAGIC
            if self._rand.getrandbits(1):
                d = (1, [i, ])
                dut.dataIn.u1.data._ag.data.append(i)
                dut.dataIn._select._ag.data.append(1)
            else:
                d = (0, [i, ])
                dut.dataIn.u0.data._ag.data.append(i)
                dut.dataIn._select._ag.data.append(0)
            ref.append(d)
        self.runSim(t * CLK_PERIOD)

        fu = Axi4StreamFrameUtils.from_HwIO(dut.dataOut)
        # reinterpret strb as keep because we would like to cut off invalidated prefix data bytes
        # to simplify checking in test
        fu.USE_STRB = False
        fu.USE_KEEP = True
        dataOutData = dut.dataOut._ag.data
        for i, ref_f in enumerate(ref):
            ref_offset, ref_data = ref_f
            f_offset, f = fu.receive_bytes(dataOutData)
            self.assertEqual(f_offset, ref_offset)
            self.assertValSequenceEqual(f, ref_data)

    def test_unionDifferentMask_randomized(self):
        self.test_unionDifferentMask(randomized=True)


if __name__ == "__main__":

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4S_frameDeparser_TC("test_struct2xStream8_0B")])
    suite = testLoader.loadTestsFromTestCase(Axi4S_frameDeparser_TC)
    runner = unittest.TextTestRunner(verbosity=3)

    runner.run(suite)
