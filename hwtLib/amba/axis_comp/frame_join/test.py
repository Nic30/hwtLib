#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import inf
import unittest

from hwt.hdl.types.bits import HBits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi4s import axi4s_recieve_bytes, axi4s_send_bytes
from hwtLib.amba.axis_comp.frame_join import Axi4S_FrameJoin
from hwtSimApi.constants import CLK_PERIOD


class Axi4S_FrameJoin_1x_1B_TC(SimTestCase):
    D_B = 1
    T = HStruct(
        (HStream(HBits(8 * D_B), (1, inf), [0]), "frame0"),
    )

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = Axi4S_FrameJoin()
        dut.T = cls.T
        dut.DATA_WIDTH = cls.D_W = cls.D_B * 8
        cls.compileSim(dut)

    def send(self, input_i, data_B, offset):
        axi4s_send_bytes(self.dut.dataIn[input_i], data_B, offset=offset)

    def recive(self):
        return axi4s_recieve_bytes(self.dut.dataOut)

    def randomize_all(self):
        for din in self.dut.dataIn:
            self.randomize(din)
        self.randomize(self.dut.dataOut)

    def gen_data(self, data_cntr, size):
        return [(data_cntr + d) & 0xff for d in range(size)]

    def test_nop(self):
        self.randomize_all()
        self.runSim(CLK_PERIOD * 20)
        self.assertEmpty(self.dut.dataOut._ag.data)

    def _test_pass_data(self, IN_FRAMES):
        OUT_FRAMES = []
        for f_i in range(len(IN_FRAMES[0])):
            offset = self.dut.OUT_OFFSET
            data = []
            for in_frames in IN_FRAMES:
                fdata = in_frames[f_i][1]
                data.extend(fdata)
            OUT_FRAMES.append((offset, data))

        for i, frames in enumerate(IN_FRAMES):
            for f_offset, frame in frames:
                self.send(i, frame, offset=f_offset)

        self.runSim(CLK_PERIOD * (
            len(IN_FRAMES) * len(OUT_FRAMES[0]) * 20 + 100))
        for (ref_offset, ref_frame) in OUT_FRAMES:
            offset, frame = axi4s_recieve_bytes(self.dut.dataOut)

            self.assertEqual(offset, ref_offset)
            self.assertSequenceEqual(frame, ref_frame)

        self.assertEmpty(self.dut.dataOut._ag.data)

    def test_pass_data_min_len(self, repeat=10):
        self.randomize_all()
        # [offset, [data]]
        IN_FRAMES = [[] for _ in self.dut.dataIn]
        data_cntr = 0
        for _ in range(repeat):
            for f, frames in zip(self.T.fields, IN_FRAMES):
                data_B = f.dtype.element_t.bit_length() // 8
                lmin = f.dtype.len_min
                # lmax = f.dtype.len_max
                # if len(f.dtype.start_offsets) != 1:
                #    raise NotImplementedError()
                for offset in f.dtype.start_offsets:
                    size = data_B * lmin
                    data = self.gen_data(data_cntr, size)
                    frames.append((offset, data))
                    data_cntr += size

        self._test_pass_data(IN_FRAMES)

    def test_pass_data_min_len_plus1(self, repeat=10):
        self.randomize_all()
        # [offset, [data]]
        IN_FRAMES = [[] for _ in self.dut.dataIn]
        data_cntr = 0
        for _ in range(repeat):
            for f, frames in zip(self.T.fields, IN_FRAMES):
                data_B = f.dtype.element_t.bit_length() // 8
                lmin = f.dtype.len_min + 1
                lmax = f.dtype.len_max
                if lmin > lmax:
                    lmin = lmax

                # if len(f.dtype.start_offsets) != 1:
                #    raise NotImplementedError()
                for offset in f.dtype.start_offsets:
                    size = data_B * lmin
                    data = self.gen_data(data_cntr, size)
                    frames.append((offset, data))
                    data_cntr += size

        self._test_pass_data(IN_FRAMES)

    def test_pass_data_min_len_plus1_for_non_first(self, repeat=10):
        if len(self.dut.dataIn) == 1:
            # test tested by test_pass_data_min_len
            return
        self.randomize_all()
        # [offset, [data]]
        IN_FRAMES = [[] for _ in self.dut.dataIn]

        data_cntr = 0
        for _ in range(repeat):
            for i, (f, frames) in enumerate(zip(self.T.fields, IN_FRAMES)):
                data_B = f.dtype.element_t.bit_length() // 8
                lmax = f.dtype.len_max
                lmin = f.dtype.len_min
                if i > 0:
                    lmin += 1

                if lmin > lmax:
                    lmin = lmax

                # if len(f.dtype.start_offsets) != 1:
                #    raise NotImplementedError()
                for offset in f.dtype.start_offsets:
                    size = data_B * lmin
                    data = self.gen_data(data_cntr, size)
                    frames.append((offset, data))
                    data_cntr += size

        self._test_pass_data(IN_FRAMES)


class Axi4S_FrameJoin_1x_2B_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * D_B), (1, inf), [0]), "frame0"),
    )


class Axi4S_FrameJoin_1x_2B_len0_inf_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * D_B), (0, inf), [0]), "frame0"),
    )


class Axi4S_FrameJoin_1x_2B_len1_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * D_B), (1, 1), [0]), "frame0"),
    )


class Axi4S_FrameJoin_2x_1B_len1_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 1
    T = HStruct(
        (HStream(HBits(8 * D_B), (1, 1), [0]), "frame0"),
        (HStream(HBits(8 * D_B), (1, 1), [0]), "frame1"),
    )


class Axi4S_FrameJoin_2x_2B_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * D_B), (1, inf), [0]), "frame0"),
        (HStream(HBits(8 * D_B), (1, inf), [0]), "frame1"),
    )

class Axi4S_FrameJoin_2x_2B_len0_inf_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * D_B), (0, 1), [0]), "frame0"),
        (HStream(HBits(8 * D_B), (0, 1), [0]), "frame1"),
    )

class Axi4S_FrameJoin_3x_2B_len0_inf_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * D_B), (0, 1), [0]), "frame0"),
        (HStream(HBits(8 * D_B), (0, 1), [0]), "frame1"),
        (HStream(HBits(8 * D_B), (0, 1), [0]), "frame2"),
    )

class Axi4S_FrameJoin_2x_1B_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 1
    T = HStruct(
        (HStream(HBits(8 * D_B), (1, inf), [0]), "frame0"),
        (HStream(HBits(8 * D_B), (1, inf), [0]), "frame1"),
    )


class Axi4S_FrameJoin_2x_1B_on_2B_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * 1), (1, inf), [0]), "frame0"),
        (HStream(HBits(8 * 1), (1, inf), [0]), "frame1"),
    )


class Axi4S_FrameJoin_2x_1B_on_2B_offset_0_1_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * 1), (1, inf), [0]), "frame0"),
        (HStream(HBits(8 * 1), (1, inf), [1]), "frame1"),
    )


class Axi4S_FrameJoin_2x_1B_on_2B_offset_1_0_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * 1), (1, inf), [1]), "frame0"),
        (HStream(HBits(8 * 1), (1, inf), [0]), "frame1"),
    )


class Axi4S_FrameJoin_2x_1B_on_2B_offset_1_1_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * 1), (1, inf), [1]), "frame0"),
        (HStream(HBits(8 * 1), (1, inf), [1]), "frame1"),
    )


class Axi4S_FrameJoin_1x_2B_offset_1_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * D_B), (1, inf), [1]), "frame0"),
    )

# class Axi4S_FrameJoin_1x_34B_offset_any_TC(Axi4S_FrameJoin_1x_1B_TC):
#    D_B = 8
#    T = HStruct(
#        (HStream(HBits(8 * 34), (1, 1), [0, 1, 2, 3, 4, 5, 6, 7]), "frame0"),
#    )


class Axi4S_FrameJoin_1x_3B_offset_0_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * 3), (1, 1), [ 0, ]), "frame0"),
    )


class Axi4S_FrameJoin_1x_3B_offset_1_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * 3), (1, 1), [ 1, ]), "frame0"),
    )


class Axi4S_FrameJoin_1x_3B_offset_0_1_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * 3), (1, 1), [0, 1, ]), "frame0"),
    )


class Axi4S_FrameJoin_1x_in_2B_offset_1__1_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * D_B), (1, inf), [1]), "frame0"),
        (HStream(HBits(8 * D_B), (1, inf), [1]), "frame1"),
    )


class Axi4S_FrameJoin_1x_in_2B_offset_1__0_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * D_B), (1, inf), [1]), "frame0"),
        (HStream(HBits(8 * D_B), (1, inf), [0]), "frame1"),
    )


class Axi4S_FrameJoin_1x_in_2B_offset_0__1_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * D_B), (1, inf), [0]), "frame0"),
        (HStream(HBits(8 * D_B), (1, inf), [1]), "frame1"),
    )


class Axi4S_FrameJoin_3x_in_2B_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * D_B), (1, inf), [0]), "frame0"),
        (HStream(HBits(8 * D_B), (1, inf), [0]), "frame1"),
        (HStream(HBits(8 * D_B), (1, inf), [0]), "frame2"),
    )


class Axi4S_FrameJoin_3x_in_1B_on_2B_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * 1), (1, inf), [0]), "frame0"),
        (HStream(HBits(8 * 1), (1, inf), [0]), "frame1"),
        (HStream(HBits(8 * 1), (1, inf), [0]), "frame2"),
    )

class Axi4S_FrameJoin_3x_in_1B_on_2B_len0_inf_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * 1), (0, inf), [0]), "frame0"),
        (HStream(HBits(8 * 1), (0, inf), [0]), "frame1"),
        (HStream(HBits(8 * 1), (0, inf), [0]), "frame2"),
    )

class Axi4S_FrameJoin_3x_in_1B_on_2B_len0_inf_in_middle_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 2
    T = HStruct(
        (HStream(HBits(8 * 1), (1, 1), [0]), "frame0"),
        (HStream(HBits(8 * 1), (0, inf), [0]), "frame1"),
        (HStream(HBits(8 * 1), (1, 1), [0]), "frame2"),
    )


class Axi4S_FrameJoin_3x_in_1B_on_5B_TC(Axi4S_FrameJoin_1x_1B_TC):
    D_B = 5
    T = HStruct(
        (HStream(HBits(8 * 1), (1, inf), [0]), "frame0"),
        (HStream(HBits(8 * 1), (1, inf), [0]), "frame1"),
        (HStream(HBits(8 * 1), (1, inf), [0]), "frame2"),
    )


Axi4S_FrameJoin_TCs = [
   Axi4S_FrameJoin_1x_1B_TC,
   Axi4S_FrameJoin_2x_1B_TC,
   Axi4S_FrameJoin_1x_2B_len1_TC,
   Axi4S_FrameJoin_2x_1B_len1_TC,
   Axi4S_FrameJoin_2x_1B_on_2B_TC,
   Axi4S_FrameJoin_2x_1B_on_2B_offset_0_1_TC,
   Axi4S_FrameJoin_2x_1B_on_2B_offset_1_0_TC,
   Axi4S_FrameJoin_2x_1B_on_2B_offset_1_1_TC,
   Axi4S_FrameJoin_1x_2B_len0_inf_TC,
   Axi4S_FrameJoin_1x_2B_TC,
   Axi4S_FrameJoin_1x_2B_offset_1_TC,
   # # Axi4S_FrameJoin_1x_34B_offset_any_TC,
   Axi4S_FrameJoin_1x_3B_offset_0_TC,
   Axi4S_FrameJoin_1x_3B_offset_1_TC,
   Axi4S_FrameJoin_1x_3B_offset_0_1_TC,
   Axi4S_FrameJoin_1x_in_2B_offset_0__1_TC,
   Axi4S_FrameJoin_1x_in_2B_offset_1__0_TC,
   Axi4S_FrameJoin_1x_in_2B_offset_1__1_TC,
   Axi4S_FrameJoin_2x_2B_TC,
   Axi4S_FrameJoin_2x_2B_len0_inf_TC,
   Axi4S_FrameJoin_3x_2B_len0_inf_TC,
   Axi4S_FrameJoin_3x_in_1B_on_2B_len0_inf_TC,
   Axi4S_FrameJoin_3x_in_1B_on_2B_len0_inf_in_middle_TC,
   Axi4S_FrameJoin_3x_in_2B_TC,
   Axi4S_FrameJoin_3x_in_1B_on_2B_TC,
   Axi4S_FrameJoin_3x_in_1B_on_5B_TC,
]

if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4S_FrameJoin_3x_in_1B_on_2B_len0_inf_TC("test_pass_data_min_len")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in Axi4S_FrameJoin_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
