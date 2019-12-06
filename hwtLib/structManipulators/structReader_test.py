#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.types.ctypes import uint64_t, uint16_t, uint32_t
from hwt.hdl.types.struct import HStruct
from hwtLib.structManipulators.structReader import StructReader
from hwtLib.abstract.denseMemory import DenseMemory
from hwt.hdl.constants import Time
from hwt.synthesizer.vectorUtils import iterBits
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl


s0 = HStruct(
    (uint64_t, "item0"),  # tuples (type, name) where type has to be instance of Bits type
    (uint64_t, None),  # name = None means this field will be ignored
    (uint64_t, "item1"),
    (uint64_t, None),
    (uint16_t, "item2"),
    (uint16_t, "item3"),
    (uint32_t, "item4"),

    (uint32_t, None),
    (uint64_t, "item5"),  # this word is split on two bus words
    (uint32_t, None),

    (uint64_t, None),
    (uint64_t, None),
    (uint64_t, None),
    (uint64_t, "item6"),
    (uint64_t, "item7"),
    )


def s0RandVal(tc):
    r = tc._rand.getrandbits
    data = {"item0": r(64),
            "item1": r(64),
            "item2": r(16),
            "item3": r(16),
            "item4": r(32),
            "item5": r(64),
            "item6": r(64),
            "item7": r(64),
            }

    return data


class StructReaderTC(SimTestCase):
    def _test_s0(self, u):
        DW = 64
        N = 3
        self.compileSimAndStart(u)

        m = DenseMemory(DW, u.clk, u.rDatapump)

        # init expectedFieldValues
        expectedFieldValues = {}
        for f in s0.fields:
            if f.name is not None:
                expectedFieldValues[f.name] = []

        for _ in range(N):
            d = s0RandVal(self)
            for name, val in d.items():
                expectedFieldValues[name].append(val)

            asFrame = list(iterBits(s0.from_py(d),
                                    bitsInOne=DW,
                                    skipPadding=False,
                                    fillup=True))
            addr = m.calloc(len(asFrame), DW // 8, initValues=asFrame)
            u.get._ag.data.append(addr)

        self.runSim(500 * Time.ns)

        for f in s0.fields:
            if f.name is not None:
                expected = expectedFieldValues[f.name]
                got = u.dataOut._fieldsToInterfaces[f]._ag.data
                self.assertValSequenceEqual(got, expected)

    def test_simpleFields(self):
        u = StructReader(s0)
        self._test_s0(u)

    def test_multiframe(self):
        tmpl = TransTmpl(s0)
        DATA_WIDTH = 64
        frames = list(FrameTmpl.framesFromTransTmpl(
                             tmpl,
                             DATA_WIDTH,
                             maxPaddingWords=0,
                             trimPaddingWordsOnStart=True,
                             trimPaddingWordsOnEnd=True))
        u = StructReader(s0, tmpl=tmpl, frames=frames)
        self._test_s0(u)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(StructReaderTC('test_regularUpload'))
    suite.addTest(unittest.makeSuite(StructReaderTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
