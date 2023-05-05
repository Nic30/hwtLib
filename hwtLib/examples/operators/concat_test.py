#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil
from typing import Dict
import unittest

from hwt.code import Concat
from hwt.hdl.constants import WRITE, READ, NOP
from hwt.hdl.types.bits import Bits
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.operators.concat import SimpleConcat, ConcatAssign, \
    ConcatIndexAssignMix0, ConcatIndexAssignMix1, ConcatIndexAssignMix2, \
    ConcatIndexAssignMix3
from hwtLib.types.net.arp import arp_ipv4_t
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import get_bit, mask


def addValues(unit, data):
    for d in data:
        # because there are 4 bits
        for i in range(4):
            databit = getattr(unit, f"a{i:d}")
            if d is None:
                dataBitval = None
            else:
                dataBitval = get_bit(d, i)

            databit._ag.data.append(dataBitval)


class ConcatTC(SimTestCase):

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def test_join(self):
        u = SimpleConcat()
        self.compileSimAndStart(u)

        # addValues(u, [0, 1, 2, 4, 8, (1 << 4) - 1, None, 3, 2, 1])
        addValues(u, [2, 4, (1 << 4) - 1, None, 3, 2, 1])
        self.runSim(7 * CLK_PERIOD)
        self.assertValSequenceEqual(u.a_out._ag.data,
                                    [2, 4, 15, None, 3, 2, 1])

    def test_assign(self):
        u = ConcatAssign()
        self.compileSimAndStart(u)
        N = 4
        a = [[] for _ in range(N)]
        for i in range(N):
            for i2, bit_ref_vals in enumerate(a):
                bit_ref_vals.append(int(i == i2))
            u.a_in._ag.data.append(1 << i)

        self.runSim(N * CLK_PERIOD)
        for i, bit_ref_vals in enumerate(a):
            data = getattr(u, f'a{i:d}')._ag.data
            self.assertValSequenceEqual(data, bit_ref_vals)

    def test_ConcatIndexAssignMix0(self):
        u = ConcatIndexAssignMix0()
        self.compileSimAndStart(u)
        N = 4
        a = [[] for _ in range(N)]
        for i in range(N):
            for i2, bit_ref_vals in enumerate(a):
                bit_ref_vals.append(int(i == i2))
            v = 1 << i
            u.a[0]._ag.data.append(v & 0x3)
            u.a[1]._ag.data.append((v >> 2) & 0x3)

        self.runSim(N * CLK_PERIOD)
        for i, bit_ref_vals in enumerate(a):
            data = u.b[i]._ag.data
            self.assertValSequenceEqual(data, bit_ref_vals)

    def test_ConcatIndexAssignMix1(self):
        u = ConcatIndexAssignMix1()
        self.compileSimAndStart(u)
        N = 4
        b = [[] for _ in range(2)]
        for i in range(N):
            for i2, a in enumerate(u.a):
                a._ag.data.append(int(i == i2))
            v = 1 << i
            b[0].append(v & 0x3)
            b[1].append((v >> 2) & 0x3)

        self.runSim(N * CLK_PERIOD)
        for i, ref_vals in enumerate(b):
            self.assertValSequenceEqual(u.b[i]._ag.data, ref_vals)

    def test_ConcatIndexAssignMix2(self):
        u = ConcatIndexAssignMix2()
        self.compileSimAndStart(u)
        N = 8
        b = [[] for _ in range(2)]
        for i in range(N):
            offset = 0
            v = 1 << i
            for a in u.a:
                w = a._dtype.bit_length()
                a._ag.data.append((v >> offset) & mask(w))
                offset += w

            b[0].append(v & 0xf)
            b[1].append((v >> 4) & 0xf)

        self.runSim(N * CLK_PERIOD)
        for i, ref_vals in enumerate(b):
            self.assertValSequenceEqual(u.b[i]._ag.data, ref_vals)

    def _ConcatIndexAssignMix3_py_val_to_words(self, v:Dict[str, int], W: int, WORD_CNT: int):
        d = arp_ipv4_t.from_py(v)
        padding_w = WORD_CNT * 24 - W
        d_words = Concat(Bits(padding_w).from_py(0), d._reinterpret_cast(Bits(W)))\
            ._reinterpret_cast(Bits(24)[WORD_CNT])
        return d_words

    def test_ConcatIndexAssignMix3(self):
        u = ConcatIndexAssignMix3()
        self.compileSimAndStart(u)
        W = arp_ipv4_t.bit_length()
        WORD_CNT = ceil(W / 24)
        D1 = self._ConcatIndexAssignMix3_py_val_to_words(
            {f.name: i + 1 for i, f in enumerate(arp_ipv4_t.fields)}, W, WORD_CNT)
        u.port._ag.requests.extend([
            NOP, NOP,
            *((READ, i) for i in range(WORD_CNT)),
            *((WRITE, i, v) for i, v in enumerate(D1)),
            *((READ, i) for i in range(WORD_CNT)),
        ])
        self.runSim((len(u.port._ag.requests) + 4) * CLK_PERIOD)
        D0 = self._ConcatIndexAssignMix3_py_val_to_words(
            {f.name: i for i, f in enumerate(arp_ipv4_t.fields)}, W, WORD_CNT)
        r_data = list(u.port._ag.r_data)
        self.assertValSequenceEqual(r_data[0:WORD_CNT] + r_data[2 * WORD_CNT:], [int(d) for d in (list(D0) + list(D1))])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([ConcatTC("test_rangeJoin")])
    suite = testLoader.loadTestsFromTestCase(ConcatTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
