from math import inf
import unittest

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwtLib.abstract.frame_join_utils.fsm import input_B_dst_to_fsm
from hwtLib.abstract.frame_join_utils.state_trans_item import StateTransItem
from hwtLib.abstract.streamAlignmentUtils import FrameJoinUtils


class FrameJoinUtilsTC(unittest.TestCase):
    def test_fsm0(self):
        word_bytes = 2
        f_len = (1, 1)
        streams = [
            HStream(Bits(8), frame_len=f_len, start_offsets=[1]),
        ]
        out_offset = 0
        sju = FrameJoinUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst)

        def st(d):
            return StateTransItem.from_dict(tt, d)

        ref = [
            [st({'st': '0->0', 'in': [[{'keep': [0, 1], 'relict': 0, 'last': 1}]],
                 'in.keep_mask':[[[0, 0]]], 'in.rd':[1],
                 'out.keep':[1, 0], 'out.mux':[(0, 0, 1), None], 'out.last':1}
                )],
        ]

        self.assertSequenceEqual(tt.state_trans, ref)

    def test_fsm0_arbitrary_len(self):
        word_bytes = 2
        f_len = (1, inf)
        streams = [
            HStream(Bits(8), frame_len=f_len),
        ]
        out_offset = 0
        sju = FrameJoinUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst)

        def st(d):
            return StateTransItem.from_dict(tt, d)

        ref = [[
            st({'st': '0->0', 'in': [[{'keep': [1, 0], 'relict': 0, 'last': 1}]],
                'in.keep_mask':[[[0, 0]]], 'in.rd':[1], 'out.keep':[1, 0],
                'out.mux':[(0, 0, 0), None], 'out.last':1}),
            st({'st': '0->0', 'in': [[{'keep': [1, 1], 'relict': 0, 'last': 1}]],
                'in.keep_mask':[[[0, 0]]], 'in.rd':[1], 'out.keep':[1, 1],
                'out.mux':[(0, 0, 0), (0, 0, 1)], 'out.last':1}),
            st({'st': '0->0', 'in': [[{'keep': [1, 1], 'relict':'X', 'last': 0}]],
                'in.keep_mask':[[[0, 0]]], 'in.rd':[1], 'out.keep':[1, 1],
                'out.mux':[(0, 0, 0), (0, 0, 1)], 'out.last':0}),
        ]]

        self.assertSequenceEqual(tt.state_trans, ref)

    def test_fsm0_arbitrary_len_unaligned(self):
        word_bytes = 2
        f_len = (1, inf)
        streams = [
            HStream(Bits(8), frame_len=f_len, start_offsets=[1]),
        ]
        out_offset = 0
        sju = FrameJoinUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst)

        def st(d):
            return StateTransItem.from_dict(tt, d)

        ref = [[
            st({'st': '0->0', 'in': [[{'keep': [0, 1], 'relict': 0, 'last': 1},
                                      {'keep': ['X', 'X'], 'relict':'X', 'last':'X'}]],
                'in.keep_mask':[[[0, 0], [1, 1]]], 'in.rd':[1],
                'out.keep':[1, 0], 'out.mux':[(0, 0, 1), None], 'out.last':1}),
            st({'st': '0->0', 'in': [[{'keep': [0, 1], 'relict': 1, 'last': 1},
                                      {'keep': ['X', 'X'], 'relict':'X', 'last':'X'}]],
                'in.keep_mask':[[[0, 0], [1, 1]]], 'in.rd':[1],
                'out.keep':[1, 0], 'out.mux':[(0, 0, 1), None], 'out.last':1}),
            st({'st': '0->0', 'in': [[{'keep': [0, 1], 'relict':'X', 'last': 0},
                                      {'keep': [1, 0], 'relict':'X', 'last': 1}]],
                'in.keep_mask':[[[0, 0], [0, 0]]], 'in.rd':[1],
                'out.keep':[1, 1], 'out.mux':[(0, 0, 1), (0, 1, 0)], 'out.last':1}),
            st({'st': '0->0', 'in': [[{'keep': [0, 1], 'relict':'X', 'last': 0},
                                      {'keep': [1, 1], 'relict':'X', 'last': 0}]],
                'in.keep_mask':[[[0, 0], [0, 1]]], 'in.rd':[1],
                'out.keep':[1, 1], 'out.mux':[(0, 0, 1), (0, 1, 0)], 'out.last':0}),
            st({'st': '0->0', 'in': [[{'keep': [0, 1], 'relict':'X', 'last': 0},
                                      {'keep': [1, 1], 'relict':'X', 'last': 1}]],
                'in.keep_mask':[[[0, 0], [0, 1]]], 'in.rd':[1],
                'out.keep':[1, 1], 'out.mux':[(0, 0, 1), (0, 1, 0)], 'out.last':0}),
        ]]
        self.assertSequenceEqual(tt.state_trans, ref)

    def test_fsm1(self):
        word_bytes = 2
        f_len = (2, 2)
        streams = [
            HStream(Bits(8), frame_len=f_len, start_offsets=[1]),
        ]
        out_offset = 0
        sju = FrameJoinUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst)

        def st(d):
            return StateTransItem.from_dict(tt, d)
        ref = [[
            st({'st': '0->0',
                'in': [[{'keep': [0, 1], 'relict':'X', 'last': 0},
                        {'keep': [1, 0], 'relict':'X', 'last': 1}]],
                'in.keep_mask':[[[0, 0], [0, 0]]], 'in.rd':[1], 'out.keep':[1, 1],
                'out.mux':[(0, 0, 1), (0, 1, 0)], 'out.last':1}
               )
        ]]

        self.assertSequenceEqual(tt.state_trans, ref)

    def test_fsm_2x1B_on_2B(self):
        word_bytes = 2
        streams = [
            HStream(Bits(8 * 1), (1, 2), [0]),
            HStream(Bits(8 * 1), (1, 2), [0]),
        ]
        out_offset = 0
        sju = FrameJoinUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst)

        def st(d):
            return StateTransItem.from_dict(tt, d)
        ref = [[
            st({'st': '0->0', 'in': [[{'keep': [1, 0], 'relict': 0, 'last': 1}],
                                     [{'keep': [1, 0], 'relict':'X', 'last': 1}]],
                'in.keep_mask':[[[0, 0]], [[0, 0]]], 'in.rd':[1, 1],
                'out.keep':[1, 1], 'out.mux':[(0, 0, 0), (1, 0, 0)], 'out.last':1}),
            st({'st': '0->1', 'in': [[{'keep': [1, 0], 'relict': 0, 'last': 1}],
                                     [{'keep': [1, 1], 'relict':'X', 'last': 1}]],
                'in.keep_mask':[[[0, 0]], [[0, 1]]], 'in.rd':[1, 1],
                'out.keep':[1, 1], 'out.mux':[(0, 0, 0), (1, 0, 0)], 'out.last':0}),
            st({'st': '0->1', 'in': [[{'keep': [1, 1], 'relict': 0, 'last': 1}],
                                     [{'keep': ['X', 'X'], 'relict':'X', 'last':'X'}]],
                'in.keep_mask':[[[0, 0]], [[1, 1]]], 'in.rd':[1, 0],
                'out.keep':[1, 1], 'out.mux':[(0, 0, 0), (0, 0, 1)], 'out.last':0})
        ], [

            st({'st': '1->0', 'in': [[{'keep': ['X', 'X'], 'relict':'X', 'last':'X'}],
                                     [{'keep': [0, 1], 'relict': 1, 'last': 1}]],
                'in.keep_mask':[[[1, 1]], [[0, 0]]], 'in.rd':[0, 1],
                'out.keep':[1, 0], 'out.mux':[(1, 0, 1), None], 'out.last':1}),
            st({'st': '1->0', 'in': [[{'keep': ['X', 'X'], 'relict':'X', 'last':'X'}],
                                     [{'keep': [1, 0], 'relict': 0, 'last': 1}]],
                'in.keep_mask':[[[1, 1]], [[0, 0]]], 'in.rd':[0, 1],
                'out.keep':[1, 0], 'out.mux':[(1, 0, 0), None], 'out.last':1}),
            st({'st': '1->0', 'in': [[{'keep': ['X', 'X'], 'relict':'X', 'last':'X'}],
                                     [{'keep': [1, 1], 'relict': 0, 'last': 1}]],
                'in.keep_mask':[[[1, 1]], [[0, 0]]], 'in.rd':[0, 1],
                'out.keep':[1, 1], 'out.mux':[(1, 0, 0), (1, 0, 1)], 'out.last':1})
        ]]
        self.assertSequenceEqual(tt.state_trans, ref)

    def test_fsm_2x1B_on_3B(self):
        word_bytes = 3
        streams = [
            HStream(Bits(8 * 1), (1, 3), [0]),
            HStream(Bits(8 * 1), (1, 3), [0]),
        ]
        out_offset = 0
        sju = FrameJoinUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst)

        def st(d):
            return StateTransItem.from_dict(tt, d)
        ref = [[st({'st': '0->0', 'in': [[{'keep': [1, 0, 'X'], 'relict': 0, 'last': 1}],
                                         [{'keep': [1, 0, 'X'], 'relict':'X', 'last': 1}]],
                    'in.keep_mask':[[[0, 0, 1]], [[0, 0, 1]]], 'in.rd':[1, 1],
                    'out.keep':[1, 1, 0], 'out.mux':[(0, 0, 0), (1, 0, 0), None], 'out.last':1}),
                st({'st': '0->0', 'in': [[{'keep': [1, 0, 'X'], 'relict': 0, 'last': 1}],
                                         [{'keep': [1, 1, 0], 'relict':'X', 'last': 1}]],
                    'in.keep_mask':[[[0, 0, 1]], [[0, 0, 0]]], 'in.rd':[1, 1],
                    'out.keep':[1, 1, 1], 'out.mux':[(0, 0, 0), (1, 0, 0), (1, 0, 1)], 'out.last':1}),
                st({'st': '0->0', 'in': [[{'keep': [1, 1, 0], 'relict': 0, 'last': 1}],
                                         [{'keep': [1, 0, 'X'], 'relict':'X', 'last': 1}]],
                    'in.keep_mask':[[[0, 0, 0]], [[0, 0, 1]]], 'in.rd':[1, 1],
                    'out.keep':[1, 1, 1], 'out.mux':[(0, 0, 0), (0, 0, 1), (1, 0, 0)], 'out.last':1}),
                st({'st': '0->1', 'in': [[{'keep': [1, 0, 'X'], 'relict': 0, 'last': 1}],
                                         [{'keep': [1, 1, 1], 'relict':'X', 'last': 1}]],
                    'in.keep_mask':[[[0, 0, 1]], [[0, 0, 1]]], 'in.rd':[1, 1],
                    'out.keep':[1, 1, 1], 'out.mux':[(0, 0, 0), (1, 0, 0), (1, 0, 1)], 'out.last':0}),
                st({'st': '0->1', 'in': [[{'keep': [1, 1, 0], 'relict': 0, 'last': 1}],
                                         [{'keep': [1, 1, 'X'], 'relict':'X', 'last': 1}]],
                    'in.keep_mask':[[[0, 0, 0]], [[0, 1, 1]]], 'in.rd':[1, 1],
                    'out.keep':[1, 1, 1], 'out.mux':[(0, 0, 0), (0, 0, 1), (1, 0, 0)], 'out.last':0}),
                st({'st': '0->1', 'in': [[{'keep': [1, 1, 1], 'relict': 0, 'last': 1}],
                                         [{'keep': ['X', 'X', 'X'], 'relict':'X', 'last':'X'}]],
                    'in.keep_mask':[[[0, 0, 0]], [[1, 1, 1]]], 'in.rd':[1, 0],
                    'out.keep':[1, 1, 1], 'out.mux':[(0, 0, 0), (0, 0, 1), (0, 0, 2)], 'out.last':0})],
               [st({'st': '1->0', 'in': [[{'keep': ['X', 'X', 'X'], 'relict':'X', 'last':'X'}],
                                         [{'keep': [0, 0, 1], 'relict': 1, 'last': 1}]],
                    'in.keep_mask':[[[1, 1, 1]], [[0, 0, 0]]], 'in.rd':[0, 1],
                    'out.keep':[1, 0, 0], 'out.mux':[(1, 0, 2), None, None], 'out.last':1}),
                st({'st': '1->0', 'in': [[{'keep': ['X', 'X', 'X'], 'relict':'X', 'last':'X'}],
                                         [{'keep': [0, 1, 0], 'relict': 1, 'last': 1}]],
                    'in.keep_mask':[[[1, 1, 1]], [[0, 0, 0]]], 'in.rd':[0, 1],
                    'out.keep':[1, 0, 0], 'out.mux':[(1, 0, 1), None, None], 'out.last':1}),
                st({'st': '1->0', 'in': [[{'keep': ['X', 'X', 'X'], 'relict':'X', 'last':'X'}],
                                         [{'keep': [0, 1, 1], 'relict': 1, 'last': 1}]],
                    'in.keep_mask':[[[1, 1, 1]], [[0, 0, 0]]], 'in.rd':[0, 1],
                    'out.keep':[1, 1, 0], 'out.mux':[(1, 0, 1), (1, 0, 2), None], 'out.last':1}),
                st({'st': '1->0', 'in': [[{'keep': ['X', 'X', 'X'], 'relict':'X', 'last':'X'}],
                                         [{'keep': [1, 0, 'X'], 'relict': 0, 'last': 1}]],
                    'in.keep_mask':[[[1, 1, 1]], [[0, 0, 1]]], 'in.rd':[0, 1],
                    'out.keep':[1, 0, 0], 'out.mux':[(1, 0, 0), None, None], 'out.last':1}),
                st({'st': '1->0', 'in': [[{'keep': ['X', 'X', 'X'], 'relict':'X', 'last':'X'}],
                                         [{'keep': [1, 1, 0], 'relict': 0, 'last': 1}]],
                    'in.keep_mask':[[[1, 1, 1]], [[0, 0, 0]]], 'in.rd':[0, 1],
                    'out.keep':[1, 1, 0], 'out.mux':[(1, 0, 0), (1, 0, 1), None], 'out.last':1}),
                st({'st': '1->0', 'in': [[{'keep': ['X', 'X', 'X'], 'relict':'X', 'last':'X'}],
                                         [{'keep': [1, 1, 1], 'relict': 0, 'last': 1}]],
                    'in.keep_mask':[[[1, 1, 1]], [[0, 0, 0]]], 'in.rd':[0, 1],
                    'out.keep':[1, 1, 1], 'out.mux':[(1, 0, 0), (1, 0, 1), (1, 0, 2)], 'out.last':1})]]
        self.assertSequenceEqual(tt.state_trans, ref)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FrameJoinUtilsTC('test_fsm_2x1B_on_2B'))
    for tc in [FrameJoinUtilsTC, ]:
        suite.addTest(unittest.makeSuite(tc))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
