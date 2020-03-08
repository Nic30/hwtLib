from math import inf
from pprint import pprint
from typing import Tuple, Dict, Set, List

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwt.pyUtils.arrayQuery import iter_with_last
from hwtLib.abstract.frame_join_utils.state_trans_info import StateTransInfo
from hwtLib.abstract.frame_join_utils.state_trans_item import StateTransItem
from hwtLib.abstract.frame_join_utils.state_trans_table import StateTransTable
from hwtLib.abstract.streamAlignmentUtils import FrameJoinUtils


def get_state_i(sub_state: StateTransInfo):
    """
    :return: min input index used during state
    """
    return min([x[0] for x in sub_state.outputs if x is not None])


def get_next_substate(sub_states: Dict[Tuple[int, int], StateTransInfo],
                      ss: StateTransInfo):
    return sub_states.get((ss.label[0], ss.label[1] + 1), None)


def is_from_different_input(a: Tuple[int, int, int, int],
                            b: Tuple[int, int, int, int],
                            ):
    return a is None \
        or b is None \
        or a[0] != b[0]


def is_next_byte_from_same_input(a: Tuple[int, int, int, int],
                                 b: Tuple[int, int, int, int],
                                 ):
    return not is_from_different_input(a, b) and a[2] == (b[2] - 1)


def input_B_dst_to_fsm(word_bytes: int,
                       input_cnt: int,
                       input_B_dst: List[List[Set[
                           Tuple[Tuple[int, int], int, int, int]
                        ]]]):
    """
    :param word_bytes: number of bytes in output word
    :param input_cnt: number of input streams
    :param input_B_dst: list with mapping of input bytes to a output bytes in each state
        Format is: List for each input
            in this list there are lists for each input byte
                in this list there are sets of byte destinations for each input byte
                    byte destination is a tuple:
                        state label, input index, time index, output byte index, input last flag
    :note: input_B_dst is produced by
        :func:`hwtLib.amba.axis_comp.frame_join_utils.FrameJoinUtils.resolve_input_bytes_destinations`
    """
    # label: StateTransInfo
    sub_states = {}
    # create substates from input byte mux info
    for in_i, in_word_dst in enumerate(input_B_dst):
        for in_B_i, in_B_dsts in enumerate(in_word_dst):
            for (st_label,
                    in_B_time,
                    out_B_i,
                    B_from_last_input_word) in in_B_dsts:
                st = sub_states.get(st_label, None)
                if st is None:
                    st = StateTransInfo(st_label, word_bytes, input_cnt)
                    sub_states[st_label] = st
                st.set_output(out_B_i, in_i, in_B_time,
                              in_B_i, B_from_last_input_word)

    # resolve max lookahead for each input
    max_lookahead_for_input = [0 for _ in range(input_cnt)]
    for in_i, in_word_dst in enumerate(input_B_dst):
        for in_B_i, in_B_dsts in enumerate(in_word_dst):
            for st_label, in_B_time, out_B_i, _ in in_B_dsts:
                max_lookahead_for_input[in_i] = max(
                    max_lookahead_for_input[in_i], in_B_time)

    # build fsm
    state_cnt = input_cnt
    tt = StateTransTable(
        word_bytes, max_lookahead_for_input, state_cnt)
    states_for_relict_processing = []
    # for all possible in/out configurations
    for ss in sorted(sub_states.values(), key=lambda x: x.label):
        st_i = get_state_i(ss)
        next_ss = get_next_substate(sub_states, ss)
        if next_ss is None:
            next_st_i = 0
        else:
            next_st_i = get_state_i(next_ss)

        tr = StateTransItem(tt)
        tt.state_trans[st_i].append(tr)
        tr.state = st_i
        tr.state_next = next_st_i
        tr.last = int(next_ss is None)
        o_prev = None
        for last, (out_B_i, o) in iter_with_last(enumerate(ss.outputs)):
            if o is None:
                o_prev = o
                # output byte is disconnected, which is default state
                continue
            # in_i - input stream index
            # in_t - input time (register index)
            (in_i, in_t, in_B_i, is_from_last_input_word) = o
            in_rec = tr.input[in_i][in_t]
            # vld, keep required as we are planing to use this byte in output
            in_rec.keep[in_B_i] = 1
            in_rec.last = is_from_last_input_word
            tr.out_byte_mux_sel[out_B_i] = (in_i, in_t, in_B_i)
            tr.input_rd[in_i] = 1
            # next keep = 0 because this byte will be consumed
            tr.input_keep_mask[in_i][in_t][in_B_i] = 0
            tr.output_keep[out_B_i] = 1

            is_first_input_byte = is_from_different_input(o_prev, o)
            # is last byte from input byte in this output word

            if last:
                o_next = next_ss.outputs[0] if next_ss is not None else None
            else:
                o_next = ss.outputs[out_B_i + 1]

            if o_next is not None:
                assert o[0] <= o_next[0]

            is_input_word_continuing_in_next_out_word = last \
                and next_ss is not None \
                and is_next_byte_from_same_input(o, o_next)\
                and in_B_i != word_bytes - 1
            if is_input_word_continuing_in_next_out_word:
                assert next_ss is not None
                states_for_relict_processing.append(next_ss)

            is_last_input_byte = is_from_different_input(o, o_next)

            if is_last_input_byte:
                assert not is_input_word_continuing_in_next_out_word

            if is_first_input_byte and in_B_i != 0:
                # mark leading zero
                for i in range(0, in_B_i):
                    in_rec.keep[i] = 0

            if (is_last_input_byte \
                    or is_input_word_continuing_in_next_out_word\
                    or last) \
                    and (
                        not (is_from_last_input_word \
                             and is_last_input_byte \
                             and in_B_i == word_bytes - 1)):
                # mark keep for next input byte
                if not is_from_last_input_word or is_input_word_continuing_in_next_out_word:
                    # the next input byte is present because we are not in last input word
                    # or this may be a last word but it is not fully consummed
                    next_B_keep = 1
                else:
                    # no more bytes from this input stream
                    next_B_keep = 0
                if in_B_i == word_bytes - 1:
                    # because pipeline will shift next time
                    in_t += 1
                input_val = tr.input[in_i]
                if in_t < len(input_val):
                    next_keep = input_val[in_t].keep
                    next_keep[(in_B_i + 1) % word_bytes] = next_B_keep
            o_prev = o
        # if we are checking the input keep==0 set keep_mask=0 as well
        # (not required, to make clear that the byte will not be used in code)
        for in_meta, in_keep_mask in zip(tr.input, tr.input_keep_mask):
            for in_i, in_inputs in enumerate(in_meta):
                for B_i, k in enumerate(in_inputs.keep):
                    if k is not None and k == 0:
                        in_keep_mask[in_i][B_i] = 0
        # mark relict flag
        first_input_is_relict = ss in states_for_relict_processing
        for o in ss.outputs:
            if o is None:
                # skip start padding
                continue

            (in_i, in_t, in_B_i, _) = o
            v = tr.input[in_i][in_t]
            if v.last:
                # relict flag matters only for word with last flag set
                # because it is used to distinguis starts of single word frames
                # where only part of the word can be consummed to a output word
                v.relict = int(first_input_is_relict)
            break
    tt.filter_unique_state_trans()
    tt.assert_transitions_deterministic()
    return tt


def example_main():
    word_bytes = 2
    f_len = (1, inf)
    streams = [
        HStream(Bits(8), frame_len=f_len, start_offsets=[1]),
        HStream(Bits(8), frame_len=f_len, start_offsets=[1]),
    ]
    out_offset = 0
    sju = FrameJoinUtils(word_bytes, out_offset)
    input_B_dst = sju.resolve_input_bytes_destinations(streams)
    tt = input_B_dst_to_fsm(word_bytes, len(streams), input_B_dst)
    pprint(tt.state_trans)


if __name__ == "__main__":
    example_main()
