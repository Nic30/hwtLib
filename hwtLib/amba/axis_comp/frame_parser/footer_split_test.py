#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from hwt.pyUtils.testUtils import TestMatrix
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4sSimFrameUtils import Axi4StreamSimFrameUtils
from hwtLib.amba.axis_comp.frame_parser.footer_split import Axi4S_footerSplit
from hwtSimApi.constants import CLK_PERIOD

TEST_FRAME_SIZES = [v * 8 for v in [
    1, 2,
    3, 4, 5, 7
]]

# [TODO] is so much of tests really necessary?
#        is mixing all possible frame sizes in single run better?


class Axi4S_footerSplitTC(SimTestCase):

    def setUp(self):
        # do avoid useless sim env reset before start (is reseted manually in each test)
        pass

    def custom_setUp(self, data_width, footer_width,
                     randomize, use_strb=False):
        dut = self.dut = Axi4S_footerSplit()
        dut.FOOTER_WIDTH = footer_width
        dut.DATA_WIDTH = data_width
        dut.USE_STRB = use_strb
        self.compileSim(dut)
        SimTestCase.setUp(self)
        if randomize:
            self.randomize_all()
        return dut

    def assertFrameEqual(self, output_i, ref_offset, ref_data):
        axis = self.dut.dataOut[output_i]
        ag_data = axis._ag.data
        fu = Axi4StreamSimFrameUtils.from_HwIO(axis)
        if fu.USE_STRB:
            # reinterpret strb as keep because we would like to cut off invalidated prefix data bytes
            # to simplify checking in test
            fu.USE_KEEP = True
            fu.USE_STRB = False
        off, data = fu.receive_bytes(ag_data)
        self.assertEqual(off, ref_offset)
        self.assertValSequenceEqual(data, ref_data)

    def randomize_all(self):
        dut = self.dut
        self.randomize(dut.dataIn)
        for i in dut.dataOut:
            self.randomize(i)

    @TestMatrix([8, 16, 24, 32],
                TEST_FRAME_SIZES,
                [False, True])
    def test_nop(self, data_width, footer_width, randomize):
        dut = self.custom_setUp(data_width, footer_width, randomize, use_strb=True)
        test_name = self.getTestName()
        unique_name = os.path.join(
            self.DEFAULT_LOG_DIR,
            f"{test_name:s}_{data_width:d}_{footer_width:d}_{randomize:d}.vcd")
        self.runSim(10 * CLK_PERIOD, name=unique_name)
        self.assertEmpty(dut.dataOut[0]._ag.data)
        self.assertEmpty(dut.dataOut[1]._ag.data)

    def _test_frames(self, data_width, footer_width,
                     frame_len0, frame_len1,
                     randomize,
                     N=3):
        dut = self.custom_setUp(data_width, footer_width,
                              randomize, use_strb=True)
        expected0 = []
        expected1 = []
        offset = 1

        def gen_data(n_bits):
            return [v & 0xff for v in range(offset, offset + n_bits // 8)]
        
        fu = Axi4StreamSimFrameUtils.from_HwIO(dut.dataIn)

        for _ in range(N):
            for frame_len in (frame_len0, frame_len1):
                fu.send_bytes(gen_data((frame_len + footer_width)), dut.dataIn._ag.data)
                expected0.append((0,
                                  gen_data(frame_len)))
                offset += frame_len // 8
                off1 = (frame_len % data_width) // 8
                expected1.append((off1,
                                  gen_data(footer_width)))
                offset += footer_width // 8

        test_name = self.getTestName()
        unique_name = os.path.join(
            self.DEFAULT_LOG_DIR,
            f"{test_name:s}_dw{data_width:d}_f{footer_width:d}_r{randomize:d}_{frame_len0:d}_{frame_len1:d}.vcd")
        t = len(dut.dataIn._ag.data)
        if randomize:
            t = int(t * 3.5)
        t += 20
        self.runSim(t * CLK_PERIOD, name=unique_name)
        for (ref_off0, ref_data0), (ref_off1, ref_data1) in zip(expected0, expected1):
            self.assertFrameEqual(0, ref_off0, ref_data0)
            self.assertFrameEqual(1, ref_off1, ref_data1)

        self.assertEmpty(dut.dataOut[0]._ag.data)
        self.assertEmpty(dut.dataOut[1]._ag.data)

    # @TestMatrix(TEST_FRAME_SIZES,
    #             TEST_FRAME_SIZES,
    #             TEST_FRAME_SIZES)
    # def test_frames_8(self, footer_width,
    #                   frame_len0, frame_len1):
    #     self._test_frames(8, footer_width, frame_len0, frame_len1, False)
    #
    # @TestMatrix(TEST_FRAME_SIZES,
    #             TEST_FRAME_SIZES,
    #             TEST_FRAME_SIZES)
    # def test_frames_16(self, footer_width,
    #                    frame_len0, frame_len1):
    #     self._test_frames(16, footer_width, frame_len0, frame_len1, False)
    #
    # @TestMatrix(TEST_FRAME_SIZES,
    #             TEST_FRAME_SIZES,
    #             TEST_FRAME_SIZES)
    # def test_frames_24(self, footer_width,
    #                    frame_len0, frame_len1):
    #     self._test_frames(24, footer_width, frame_len0, frame_len1, False)

    @TestMatrix(TEST_FRAME_SIZES,
                [0, ] + TEST_FRAME_SIZES,
                [0, ] + TEST_FRAME_SIZES)
    def test_frames_8b_randomized(self, footer_width,
                                 frame_len0, frame_len1):
        self._test_frames(8, footer_width, frame_len0, frame_len1, False)

    @TestMatrix(TEST_FRAME_SIZES,
                [0, ] + TEST_FRAME_SIZES,
                [0, ] + TEST_FRAME_SIZES)
    def test_frames_16b_randomized(self, footer_width,
                                  frame_len0, frame_len1):
        self._test_frames(16, footer_width, frame_len0, frame_len1, True)

    @TestMatrix(TEST_FRAME_SIZES,
                [0, ] + TEST_FRAME_SIZES,
                [0, ] + TEST_FRAME_SIZES)
    def test_frames_24b_randomized(self, footer_width,
                                  frame_len0, frame_len1):
        self._test_frames(24, footer_width, frame_len0, frame_len1, True)


if __name__ == '__main__':
    import unittest
    try:
        from concurrencytest import ConcurrentTestSuite, fork_for_tests
        useParallelTest = True
    except ImportError:
        # concurrencytest is not installed, use regular test runner
        useParallelTest = False
    # useParallelTest = False

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4S_footerSplitTC("test_frames_16b_randomized")])
    suite = testLoader.loadTestsFromTestCase(Axi4S_footerSplitTC)
    
    runner = unittest.TextTestRunner(verbosity=3)
    if useParallelTest:
        # Run same tests across multiple processes
        concurrent_suite = ConcurrentTestSuite(suite, fork_for_tests())
        runner.run(concurrent_suite)
    else:
        runner.run(suite)
