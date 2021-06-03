#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from hwt.pyUtils.testUtils import TestMatrix
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis import axis_send_bytes, axis_recieve_bytes
from hwtLib.amba.axis_comp.frame_parser.footer_split import AxiS_footerSplit
from hwtSimApi.constants import CLK_PERIOD

TEST_FRAME_SIZES = [v * 8 for v in [
    1, 2,
    3, 4, 5, 7
]]

# [TODO] is so much of tests really necessary?
#        is mixing all possible frame sizes in single run better?


class AxiS_footerSplitTC(SimTestCase):

    def setUp(self):
        # do avoid useless sim env reset before start (is reseted manually in each test)
        pass

    def custom_setUp(self, data_width, footer_width,
                     randomize, use_strb=False):
        u = self.u = AxiS_footerSplit()
        u.FOOTER_WIDTH = footer_width
        u.DATA_WIDTH = data_width
        u.USE_STRB = use_strb
        self.compileSim(u)
        SimTestCase.setUp(self)
        if randomize:
            self.randomize_all()
        return u

    def assertFrameEqual(self, output_i, ref_offset, ref_data):
        off, data = axis_recieve_bytes(self.u.dataOut[output_i])
        self.assertEqual(off, ref_offset)
        self.assertValSequenceEqual(data, ref_data)

    def randomize_all(self):
        u = self.u
        self.randomize(u.dataIn)
        for i in u.dataOut:
            self.randomize(i)

    @TestMatrix([8, 16, 24, 32],
                TEST_FRAME_SIZES,
                [False, True])
    def test_nop(self, data_width, footer_width, randomize):
        u = self.custom_setUp(data_width, footer_width, randomize, use_strb=True)
        test_name = self.getTestName()
        unique_name = os.path.join(
            self.DEFAULT_LOG_DIR,
            f"{test_name:s}_{data_width:d}_{footer_width:d}_{randomize:d}.vcd")
        self.runSim(10 * CLK_PERIOD, name=unique_name)
        self.assertEmpty(u.dataOut[0]._ag.data)
        self.assertEmpty(u.dataOut[1]._ag.data)

    def _test_frames(self, data_width, footer_width,
                     frame_len0, frame_len1,
                     randomize,
                     N=3):
        u = self.custom_setUp(data_width, footer_width,
                              randomize, use_strb=True)
        expected0 = []
        expected1 = []
        offset = 1

        def gen_data(n_bits):
            return [v & 0xff for v in range(offset, offset + n_bits // 8)]

        for _ in range(N):
            for frame_len in (frame_len0, frame_len1):
                axis_send_bytes(u.dataIn, gen_data((frame_len + footer_width)))
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
        t = len(u.dataIn._ag.data)
        if randomize:
            t = int(t * 3.5)
        t += 20
        self.runSim(t * CLK_PERIOD, name=unique_name)
        for (ref_off0, ref_data0), (ref_off1, ref_data1) in zip(expected0, expected1):
            self.assertFrameEqual(0, ref_off0, ref_data0)
            self.assertFrameEqual(1, ref_off1, ref_data1)

        self.assertEmpty(u.dataOut[0]._ag.data)
        self.assertEmpty(u.dataOut[1]._ag.data)

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
    def test_frames_8_randomized(self, footer_width,
                                 frame_len0, frame_len1):
        self._test_frames(8, footer_width, frame_len0, frame_len1, False)

    @TestMatrix(TEST_FRAME_SIZES,
                [0, ] + TEST_FRAME_SIZES,
                [0, ] + TEST_FRAME_SIZES)
    def test_frames_16_randomized(self, footer_width,
                                  frame_len0, frame_len1):
        self._test_frames(16, footer_width, frame_len0, frame_len1, True)

    @TestMatrix(TEST_FRAME_SIZES,
                [0, ] + TEST_FRAME_SIZES,
                [0, ] + TEST_FRAME_SIZES)
    def test_frames_24_randomized(self, footer_width,
                                  frame_len0, frame_len1):
        self._test_frames(24, footer_width, frame_len0, frame_len1, True)


if __name__ == '__main__':
    import unittest
    try:
        from concurrencytest import ConcurrentTestSuite, fork_for_tests
        useParallerlTest = True
    except ImportError:
        # concurrencytest is not installed, use regular test runner
        useParallerlTest = False
    # useParallerlTest = False

    suite = unittest.TestSuite()
    # suite.addTest(AxiS_footerSplitTC('test_nop'))
    # suite.addTest(AxiS_footerSplitTC('test_frames_8'))
    # suite.addTest(AxiS_footerSplitTC('test_frames_16'))
    # suite.addTest(AxiS_footerSplitTC('test_frames_24'))
    # suite.addTest(AxiS_footerSplitTC('test_frames_8_randomized'))
    suite.addTest(unittest.makeSuite(AxiS_footerSplitTC))
    runner = unittest.TextTestRunner(verbosity=3)
    if useParallerlTest:
        # Run same tests across multiple processes
        concurrent_suite = ConcurrentTestSuite(suite, fork_for_tests())
        runner.run(concurrent_suite)
    else:
        runner.run(suite)
