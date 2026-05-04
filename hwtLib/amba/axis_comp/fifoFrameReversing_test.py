#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdlConvertorAst.to.hdlUtils import iter_with_last
from hwt.constants import Time
from hwt.serializer.combLoopAnalyzer import CombLoopAnalyzer
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.fifoFrameReversing import Axi4S_fifoFrameReversing
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer


class Axi4S_fifoFrameReversing_MAX_PKT_WORDS_2(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = Axi4S_fifoFrameReversing()
        cls.dut = dut
        dut.DATA_WIDTH = 8
        dut.USE_STRB = False
        dut.MAX_PKT_WORDS = 2
        dut.MAX_PKT_CNT = 2
        dut.DEPTH = dut.MAX_PKT_WORDS * dut.MAX_PKT_CNT

        cls.compileSim(dut)

    def test_no_comb_loops(self):
        CombLoopAnalyzer.check_comb_loops_in_SimTestCase(self)

    def test_nop(self):
        dut = self.dut
        self.runSim(20 * CLK_PERIOD)
        self.assertEqual(len(dut.dataOut._ag.data), 0)

    def test_singleWordPacket(self):
        dut = self.dut

        dut.dataIn._ag.data.extend([
            (2, 1),
        ])

        self.runSim(20 * CLK_PERIOD)
        self.assertValSequenceEqual(dut.dataOut._ag.data, [
            (2, 1),
        ])

    def test_multiplePackets(self):
        dut = self.dut
        data = dut.dataOut._ag.data

        goldenData = [(1, 1),
                      (2, 1),
                      (3, 1)
                      ]

        dut.dataIn._ag.data.extend(goldenData)

        self.runSim(20 * CLK_PERIOD)
        self.assertValSequenceEqual(data, goldenData)

    def test_doubleWordPacket(self):
        dut = self.dut
        data = dut.dataOut._ag.data

        goldenData = [(1, 0),
                      (2, 1)
                      ]
        dut.dataIn._ag.data.extend(goldenData)

        self.runSim(20 * CLK_PERIOD)
        self.assertValSequenceEqual(data, self.model(goldenData))

    def model(self, inFrameWords: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """
        reverse words in frames
        """
        frame = []
        result = []
        for word in inFrameWords:
            d, last = word
            frame.append(d)
            if last:
                result.extend((d, int(isLast)) for isLast, d in iter_with_last(reversed(frame)))
                frame.clear()

        return result

    def test_withOutPause(self):
        dut = self.dut
        data = dut.dataOut._ag.data

        goldenData = [
            (i + 1, int(i == 5)) for i in range(min(dut.MAX_PKT_WORDS, 6))
        ]
        dut.dataIn._ag.data.extend(goldenData)

        def pause():
            yield Timer(3 * CLK_PERIOD)
            dut.dataOut._ag.setEnable_asMonitor(False)
            yield Timer(3 * CLK_PERIOD)
            dut.dataOut._ag.setEnable_asMonitor(True)

        self.procs.append(pause())

        self.runSim(20 * CLK_PERIOD)

        self.assertValSequenceEqual(data, self.model(goldenData))

    def test_withInPause(self):
        dut = self.dut
        data = dut.dataOut._ag.data

        goldenData = [
            (i + 1, int(i == 5)) for i in range(min(dut.MAX_PKT_WORDS, 6))
        ]
        dut.dataIn._ag.data.extend(goldenData)

        def pause():
            yield Timer(3 * CLK_PERIOD)
            dut.dataIn._ag.setEnable_asDriver(False)
            yield Timer(3 * CLK_PERIOD)
            dut.dataIn._ag.setEnable_asDriver(True)

        self.procs.append(pause())

        self.runSim(20 * CLK_PERIOD)

        self.assertValSequenceEqual(data, self.model(goldenData))

    def test_randomized(self, N=30):
        dut = self.dut

        inputWords = []
        off = 0
        for i in range(N):
            d = [
                ((off + i + 1) & 0xff, i == 5) for i in range(min(dut.MAX_PKT_WORDS, 6))
            ]
            inputWords.extend(d)
            off += len(d)
        dut.dataIn._ag.data.extend(inputWords)
        self.randomize(dut.dataIn)
        self.randomize(dut.dataOut)

        self.runSim(N * 6 * 3 * 10 * Time.ns)

        data = dut.dataOut._ag.data
        self.assertValSequenceEqual(data, self.model(inputWords))

    def test_randomized10(self, N=6):
        dut = self.dut
        data = dut.dataOut._ag.data

        inputWords = []
        off = 0
        for i in range(N):
            _l = 1 + int(self._rand.random() * dut.MAX_PKT_WORDS)
            assert _l <= dut.MAX_PKT_WORDS
            d = [((off + i + 1) & 0xff, int(i == (_l - 1))) for i in range(_l)]
            off += len(d)
            inputWords.extend(d)
        dut.dataIn._ag.data.extend(inputWords)

        self.randomize(dut.dataIn)
        dut.dataIn._ag.presetBeforeClk = True
        self.randomize(dut.dataOut)

        self.runSim(len(inputWords) * 12 * CLK_PERIOD)

        ref = self.model(inputWords)
        # for (w, wRef) in zip(data, ref):
        #    w = (int(w[0]), int(w[1]))
        #    print(w, wRef, "<<<" if w != wRef else '')
        #
        # self.asserEqual(len(data), len(ref))
        self.assertValSequenceEqual(data, ref)


class Axi4S_fifoFrameReversing_MAX_PKT_WORDS_3(Axi4S_fifoFrameReversing_MAX_PKT_WORDS_2):

    @classmethod
    def setUpClass(cls):
        dut = Axi4S_fifoFrameReversing()
        cls.dut = dut
        dut.DATA_WIDTH = 8
        dut.USE_STRB = False
        dut.MAX_PKT_WORDS = 4 - 1
        dut.MAX_PKT_CNT = 2
        dut.DEPTH = dut.MAX_PKT_WORDS * dut.MAX_PKT_CNT

        cls.compileSim(dut)


class Axi4S_fifoFrameReversing_MAX_PKT_WORDS_4(Axi4S_fifoFrameReversing_MAX_PKT_WORDS_2):

    @classmethod
    def setUpClass(cls):
        dut = Axi4S_fifoFrameReversing()
        cls.dut = dut
        dut.DATA_WIDTH = 8
        dut.USE_STRB = False
        dut.MAX_PKT_WORDS = 4
        dut.MAX_PKT_CNT = 2
        dut.DEPTH = dut.MAX_PKT_WORDS * dut.MAX_PKT_CNT

        cls.compileSim(dut)


Axi4S_fifoFrameReversing_TCs = [
    Axi4S_fifoFrameReversing_MAX_PKT_WORDS_2,
    Axi4S_fifoFrameReversing_MAX_PKT_WORDS_3,
    Axi4S_fifoFrameReversing_MAX_PKT_WORDS_4,
]

if __name__ == "__main__":
    import unittest

    testLoader = unittest.TestLoader()
    suite = unittest.TestSuite([testLoader.loadTestsFromTestCase(tc) for tc in Axi4S_fifoFrameReversing_TCs])
    # suite = testLoader.loadTestsFromTestCase(Axi4S_fifoFrameReversing_MAX_PKT_WORDS_2)
    # suite = unittest.TestSuite([Axi4S_fifoFrameReversing_MAX_PKT_WORDS_2("test_withInPause")])
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

