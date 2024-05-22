#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil
from typing import Dict
import unittest

from hwt.code import Concat
from hwt.constants import WRITE, READ, NOP
from hwt.hdl.types.bits import HBits
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.operators.concat import SimpleConcat, ConcatAssign, \
    ConcatIndexAssignMix0, ConcatIndexAssignMix1, ConcatIndexAssignMix2, \
    ConcatIndexAssignMix3
from hwtLib.types.net.arp import arp_ipv4_t
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import get_bit, mask


def addValues(m: SimpleConcat, data):
    for d in data:
        # because there are 4 bits
        for i in range(4):
            databit = getattr(m, f"a{i:d}")
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
        dut = SimpleConcat()
        self.compileSimAndStart(dut)

        # addValues(dut, [0, 1, 2, 4, 8, (1 << 4) - 1, None, 3, 2, 1])
        addValues(dut, [2, 4, (1 << 4) - 1, None, 3, 2, 1])
        self.runSim(7 * CLK_PERIOD)
        self.assertValSequenceEqual(dut.a_out._ag.data,
                                    [2, 4, 15, None, 3, 2, 1])

    def test_assign(self):
        dut = ConcatAssign()
        self.compileSimAndStart(dut)
        N = 4
        a = [[] for _ in range(N)]
        for i in range(N):
            for i2, bit_ref_vals in enumerate(a):
                bit_ref_vals.append(int(i == i2))
            dut.a_in._ag.data.append(1 << i)

        self.runSim(N * CLK_PERIOD)
        for i, bit_ref_vals in enumerate(a):
            data = getattr(dut, f'a{i:d}')._ag.data
            self.assertValSequenceEqual(data, bit_ref_vals)

    def test_ConcatIndexAssignMix0(self):
        dut = ConcatIndexAssignMix0()
        self.compileSimAndStart(dut)
        N = 4
        a = [[] for _ in range(N)]
        for i in range(N):
            for i2, bit_ref_vals in enumerate(a):
                bit_ref_vals.append(int(i == i2))
            v = 1 << i
            dut.a[0]._ag.data.append(v & 0x3)
            dut.a[1]._ag.data.append((v >> 2) & 0x3)

        self.runSim(N * CLK_PERIOD)
        for i, bit_ref_vals in enumerate(a):
            data = dut.b[i]._ag.data
            self.assertValSequenceEqual(data, bit_ref_vals)

    def test_ConcatIndexAssignMix1(self):
        dut = ConcatIndexAssignMix1()
        self.compileSimAndStart(dut)
        N = 4
        b = [[] for _ in range(2)]
        for i in range(N):
            for i2, a in enumerate(dut.a):
                a._ag.data.append(int(i == i2))
            v = 1 << i
            b[0].append(v & 0x3)
            b[1].append((v >> 2) & 0x3)

        self.runSim(N * CLK_PERIOD)
        for i, ref_vals in enumerate(b):
            self.assertValSequenceEqual(dut.b[i]._ag.data, ref_vals)

    def test_ConcatIndexAssignMix2(self):
        dut = ConcatIndexAssignMix2()
        self.compileSimAndStart(dut)
        N = 8
        b = [[] for _ in range(2)]
        for i in range(N):
            offset = 0
            v = 1 << i
            for a in dut.a:
                w = a._dtype.bit_length()
                a._ag.data.append((v >> offset) & mask(w))
                offset += w

            b[0].append(v & 0xf)
            b[1].append((v >> 4) & 0xf)

        self.runSim(N * CLK_PERIOD)
        for i, ref_vals in enumerate(b):
            self.assertValSequenceEqual(dut.b[i]._ag.data, ref_vals)

    def _ConcatIndexAssignMix3_py_val_to_words(self, v:Dict[str, int], W: int, WORD_CNT: int):
        d = arp_ipv4_t.from_py(v)
        padding_w = WORD_CNT * 24 - W
        d_words = Concat(HBits(padding_w).from_py(0), d._reinterpret_cast(HBits(W)))\
            ._reinterpret_cast(HBits(24)[WORD_CNT])
        return d_words

    def test_ConcatIndexAssignMix3(self):
        dut = ConcatIndexAssignMix3()
        self.compileSimAndStart(dut)
        W = arp_ipv4_t.bit_length()
        WORD_CNT = ceil(W / 24)
        D1 = self._ConcatIndexAssignMix3_py_val_to_words(
            {f.name: i + 1 for i, f in enumerate(arp_ipv4_t.fields)}, W, WORD_CNT)
        dut.port._ag.requests.extend([
            NOP, NOP,
            *((READ, i) for i in range(WORD_CNT)),
            *((WRITE, i, v) for i, v in enumerate(D1)),
            *((READ, i) for i in range(WORD_CNT)),
        ])
        self.runSim((len(dut.port._ag.requests) + 4) * CLK_PERIOD)
        D0 = self._ConcatIndexAssignMix3_py_val_to_words(
            {f.name: i for i, f in enumerate(arp_ipv4_t.fields)}, W, WORD_CNT)
        r_data = list(dut.port._ag.r_data)
        self.assertValSequenceEqual(r_data[0:WORD_CNT] + r_data[2 * WORD_CNT:], [int(d) for d in (list(D0) + list(D1))])


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([ConcatTC("test_rangeJoin")])
    suite = testLoader.loadTestsFromTestCase(ConcatTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
