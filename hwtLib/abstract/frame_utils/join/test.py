from math import inf
import unittest

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwtLib.abstract.frame_utils.alignment_utils import FrameAlignmentUtils
from hwtLib.abstract.frame_utils.join.fsm import input_B_dst_to_fsm
from hwtLib.abstract.frame_utils.join.state_trans_item import StateTransItem


class FrameJoinUtilsTC(unittest.TestCase):

    def test_fsm0(self):
        word_bytes = 2
        f_len = (1, 1)
        streams = [
            HStream(Bits(8), frame_len=f_len, start_offsets=[1]),
        ]
        out_offset = 0
        sju = FrameAlignmentUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst, sju.can_produce_zero_len_frame(streams))

        def st(d):
            return StateTransItem.from_dict(tt, d)

        ref = [[
            st({'st': '0->0', 'in': [[{'keep': [0, 1], 'relict': 0, 'last': 1}]],
                 'in.keep_mask':[[[0, 0]]], 'in.rd':[1],
                 'out.keep':[1, 0], 'out.mux':[(0, 0, 1), None], 'out.last':1}
                )],
        ]

        self.assertSequenceEqual(tt.state_trans, ref)

    def test_fsm0_w2_0B(self):
        word_bytes = 2
        streams = [
            HStream(Bits(8), frame_len=(0, 1)),
        ]
        out_offset = 0
        sju = FrameAlignmentUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst, sju.can_produce_zero_len_frame(streams))

        def st(d):
            return StateTransItem.from_dict(tt, d)

        ref = [[
            st({'st':'0->0', 'in':[[{'keep':[0, 0], 'relict':1, 'last':1}]],
                'in.keep_mask':[[[0, 0]]], 'in.rd':[1],
                'out.keep':[0, 0], 'out.mux':[None, None], 'out.last':1}),
            st({'st':'0->0', 'in':[[{'keep':[1, 0], 'relict':0, 'last':1}]],
                'in.keep_mask':[[[0, 0]]], 'in.rd':[1],
                'out.keep':[1, 0], 'out.mux':[(0, 0, 0), None], 'out.last':1})
        ]]
        self.assertSequenceEqual(tt.state_trans, ref)

    def test_fsm0_0B(self):
        word_bytes = 1
        streams = [
            HStream(Bits(8), frame_len=(0, 1)),
        ]
        out_offset = 0
        sju = FrameAlignmentUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst, sju.can_produce_zero_len_frame(streams))

        def st(d):
            return StateTransItem.from_dict(tt, d)

        ref = [[
            st({'st':'0->0', 'in':[[{'keep':[0], 'relict':1, 'last':1}]],
                'in.keep_mask':[[[0]]], 'in.rd':[1],
                'out.keep':[0], 'out.mux':[None], 'out.last':1}),
            st({'st':'0->0', 'in':[[{'keep':[1], 'relict':0, 'last':1}]],
                'in.keep_mask':[[[0]]], 'in.rd':[1],
                'out.keep':[1], 'out.mux':[(0, 0, 0)], 'out.last':1})
        ]]

        self.assertSequenceEqual(tt.state_trans, ref)

    def test_fsm0_arbitrary_len(self):
        word_bytes = 2
        f_len = (1, inf)
        streams = [
            HStream(Bits(8), frame_len=f_len),
        ]
        out_offset = 0
        sju = FrameAlignmentUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst, sju.can_produce_zero_len_frame(streams))

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
        sju = FrameAlignmentUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst, sju.can_produce_zero_len_frame(streams))

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
        sju = FrameAlignmentUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst, sju.can_produce_zero_len_frame(streams))

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
        sju = FrameAlignmentUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst, sju.can_produce_zero_len_frame(streams))

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

    def test_fsm_2x0to2B_on_2B(self):
        word_bytes = 2
        streams = [
            HStream(Bits(8 * 1), (0, 2), [0]),
            HStream(Bits(8 * 1), (0, 2), [0]),
        ]
        out_offset = 0
        sju = FrameAlignmentUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst, sju.can_produce_zero_len_frame(streams))

        def st(d):
            return StateTransItem.from_dict(tt, d)

        ref = [
            [
              st({'st':'0->0', 'in':[[{'keep':[0, 0], 'relict':1, 'last':1}], [{'keep':[0, 0], 'relict':1, 'last':1}]],
                'in.keep_mask':[[[0, 0]], [[0, 0]]], 'in.rd':[1, 1],
                'out.keep':[0, 0], 'out.mux':[None, None], 'out.last':1}),
              st({'st':'0->0', 'in':[[{'keep':[0, 0], 'relict':1, 'last':1}], [{'keep':[0, 1], 'relict':1, 'last':1}]],
                'in.keep_mask':[[[0, 0]], [[0, 0]]], 'in.rd':[1, 1],
                'out.keep':[1, 0], 'out.mux':[(1, 0, 1), None], 'out.last':1}),
              st({'st':'0->0', 'in':[[{'keep':[0, 0], 'relict':1, 'last':1}], [{'keep':[1, 0], 'relict':0, 'last':1}]],
                'in.keep_mask':[[[0, 0]], [[0, 0]]], 'in.rd':[1, 1],
                'out.keep':[1, 0], 'out.mux':[(1, 0, 0), None], 'out.last':1}),
              st({'st':'0->0', 'in':[[{'keep':[0, 0], 'relict':1, 'last':1}], [{'keep':[1, 1], 'relict':0, 'last':1}]],
                'in.keep_mask':[[[0, 0]], [[0, 0]]], 'in.rd':[1, 1],
                'out.keep':[1, 1], 'out.mux':[(1, 0, 0), (1, 0, 1)], 'out.last':1}),
              st({'st':'0->0', 'in':[[{'keep':[1, 0], 'relict':0, 'last':1}], [{'keep':[0, 0], 'relict':1, 'last':1}]],
                'in.keep_mask':[[[0, 0]], [[0, 0]]], 'in.rd':[1, 1],
                'out.keep':[1, 0], 'out.mux':[(0, 0, 0), None], 'out.last':1}),
              st({'st':'0->0', 'in':[[{'keep':[1, 0], 'relict':0, 'last':1}], [{'keep':[1, 0], 'relict':'X', 'last':1}]],
                'in.keep_mask':[[[0, 0]], [[0, 0]]], 'in.rd':[1, 1],
                'out.keep':[1, 1], 'out.mux':[(0, 0, 0), (1, 0, 0)], 'out.last':1}),
              st({'st':'0->0', 'in':[[{'keep':[1, 1], 'relict':0, 'last':1}], [{'keep':[0, 0], 'relict':1, 'last':1}]],
                'in.keep_mask':[[[0, 0]], [[0, 0]]], 'in.rd':[1, 1],
                'out.keep':[1, 1], 'out.mux':[(0, 0, 0), (0, 0, 1)], 'out.last':1}),
              st({'st':'0->1', 'in':[[{'keep':[1, 0], 'relict':0, 'last':1}], [{'keep':[1, 1], 'relict':'X', 'last':1}]],
                'in.keep_mask':[[[0, 0]], [[0, 1]]], 'in.rd':[1, 1],
                'out.keep':[1, 1], 'out.mux':[(0, 0, 0), (1, 0, 0)], 'out.last':0}),
              st({'st':'0->1', 'in':[[{'keep':[1, 1], 'relict':0, 'last':1}], [{'keep':[1, 'X'], 'relict':'X', 'last':'X'}]],
                'in.keep_mask':[[[0, 0]], [[1, 1]]], 'in.rd':[1, 0],
                'out.keep':[1, 1], 'out.mux':[(0, 0, 0), (0, 0, 1)], 'out.last':0}),
            ], [
              st({'st':'1->0', 'in':[[{'keep':['X', 'X'], 'relict':'X', 'last':'X'}], [{'keep':[0, 1], 'relict':1, 'last':1}]],
                'in.keep_mask':[[[1, 1]], [[0, 0]]], 'in.rd':[0, 1],
                'out.keep':[1, 0], 'out.mux':[(1, 0, 1), None], 'out.last':1}),
              st({'st':'1->0', 'in':[[{'keep':['X', 'X'], 'relict':'X', 'last':'X'}], [{'keep':[1, 0], 'relict':0, 'last':1}]],
                'in.keep_mask':[[[1, 1]], [[0, 0]]], 'in.rd':[0, 1],
                'out.keep':[1, 0], 'out.mux':[(1, 0, 0), None], 'out.last':1}),
              st({'st':'1->0', 'in':[[{'keep':['X', 'X'], 'relict':'X', 'last':'X'}], [{'keep':[1, 1], 'relict':0, 'last':1}]],
                'in.keep_mask':[[[1, 1]], [[0, 0]]], 'in.rd':[0, 1],
                'out.keep':[1, 1], 'out.mux':[(1, 0, 0), (1, 0, 1)], 'out.last':1}),
            ],
        ]
        # print("[")
        # for st in tt.state_trans:
        #     print("[")
        #     for t in st:
        #         t:StateTransItem
        #         print("  st(%s)," % t.__repr__(as_dict=True))
        #     print("],")
        # print("]")
        self.assertSequenceEqual(tt.state_trans, ref)

    def test_fsm_2x1B_on_3B(self):
        word_bytes = 3
        streams = [
            HStream(Bits(8 * 1), (1, 3), [0]),
            HStream(Bits(8 * 1), (1, 3), [0]),
        ]
        out_offset = 0
        sju = FrameAlignmentUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst, sju.can_produce_zero_len_frame(streams))

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

    def test_fsm_1x3B_on_2B_offset_1(self):
        word_bytes = 2
        streams = [
            HStream(Bits(8 * 3), (1, 1), [1]),
        ]
        out_offset = 0
        sju = FrameAlignmentUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst, sju.can_produce_zero_len_frame(streams))

        def st(d):
            return StateTransItem.from_dict(tt, d)

        ref = [[
            st({'st':'0->0', 'in':[[{'keep':[ 0 , 1 ], 'relict': 1 , 'last': 1 },
                                    {'keep':['X', 'X'], 'relict':'X', 'last':'X'}]],
                 'in.keep_mask':[[[0, 0], [1, 1]]], 'in.rd':[1],
                 'out.keep':[1, 0], 'out.mux':[(0, 0, 1), None], 'out.last':1}),
            st({'st':'0->0', 'in':[[{'keep':[ 0 , 1 ], 'relict':'X', 'last': 0 },
                                    {'keep':[ 1 , 1 ], 'relict':'X', 'last': 1 }]],
                 'in.keep_mask':[[[0, 0], [0, 1]]], 'in.rd':[1],
                 'out.keep':[1, 1], 'out.mux':[(0, 0, 1), (0, 1, 0)], 'out.last':0})
        ]]
        self.assertSequenceEqual(tt.state_trans, ref)

    def test_fsm_1x3B_on_2B_offset_0_1(self):
        word_bytes = 2
        streams = [
            HStream(Bits(8 * 3), (1, 1), [0, 1]),
        ]
        out_offset = 0
        sju = FrameAlignmentUtils(word_bytes, out_offset)
        input_B_dst = sju.resolve_input_bytes_destinations(streams)
        tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst, sju.can_produce_zero_len_frame(streams))

        def st(d):
            return StateTransItem.from_dict(tt, d)

        ref = [[
            st({'st':'0->0', 'in':[[{'keep':[ 0 , 1 ], 'relict': 1 , 'last': 1 },  # w 1, off 0
                                    {'keep':['X', 'X'], 'relict':'X', 'last':'X'}]],
                'in.keep_mask':[[[0, 0], [1, 1]]], 'in.rd':[1],
                'out.keep':[1, 0], 'out.mux':[(0, 0, 1), None], 'out.last':1}),
            st({'st':'0->0', 'in':[[{'keep':[ 0 , 1 ], 'relict':'X', 'last': 0 },  # w 0, off 1
                                    {'keep':[ 1 , 1 ], 'relict':'X', 'last': 1 }]],  # w 1, off 1
                'in.keep_mask':[[[0, 0], [0, 1]]], 'in.rd':[1],
                'out.keep':[1, 1], 'out.mux':[(0, 0, 1), (0, 1, 0)], 'out.last':0}),
            st({'st':'0->0', 'in':[[{'keep':[ 1 , 0 ], 'relict': 0 , 'last': 1 },  # w 1
                                    {'keep':['X', 'X'], 'relict':'X', 'last':'X'}]],
                'in.keep_mask':[[[0, 0], [1, 1]]], 'in.rd':[1],
                'out.keep':[1, 0], 'out.mux':[(0, 0, 0), None], 'out.last':1}),
            st({'st':'0->0', 'in':[[{'keep':[ 1 , 1 ], 'relict':'X', 'last': 0 },
                                    {'keep':[ 1 , 'X'], 'relict':'X', 'last':'X'}]],
                'in.keep_mask':[[[0, 0], [1, 1]]], 'in.rd':[1],
                'out.keep':[1, 1], 'out.mux':[(0, 0, 0), (0, 0, 1)], 'out.last':0})
        ]]
        self.assertSequenceEqual(tt.state_trans, ref)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FrameJoinUtilsTC('test_fsm0_0B'))
    for tc in [FrameJoinUtilsTC, ]:
        suite.addTest(unittest.makeSuite(tc))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
