from typing import Tuple, Dict, Set, List

from hwt.pyUtils.arrayQuery import iter_with_last
from hwtLib.abstract.frame_utils.join.state_trans_info import StateTransInfo
from hwtLib.abstract.frame_utils.join.state_trans_item import StateTransItem
from hwtLib.abstract.frame_utils.join.state_trans_table import StateTransTable
from hwtLib.abstract.frame_utils.join.input_reg_val import InputRegInputVal
from copy import deepcopy


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
                        ]]],
                       can_be_zero_len_frame: List[bool]):
    """
    :param word_bytes: number of bytes in output word
    :param input_cnt: number of input streams
    :param input_B_dst: list with mapping of input bytes to a output bytes in each state

    .. code-block::

        Format of input_B_dst is: List for each input
            in this list there are lists for each input byte
                in this list there are sets of byte destinations for each input byte
                    byte destination is a tuple:
                        state label, input index, time index, output byte index, input last flag

    :note: input_B_dst is produced by :func:`hwtLib.amba.axis_comp.frame_utils.join.FrameJoinUtils.resolve_input_bytes_destinations`
    """
    # (out_frame_format_i, out_word_i): StateTransInfo
    sub_states: Dict[Tuple[int, int], StateTransInfo] = {}
    # create substates from input byte mux info
    for in_i, in_word_dst in enumerate(input_B_dst):
        for in_B_i, in_B_dsts in enumerate(in_word_dst):
            for (st_label,
                    in_B_time,
                    out_B_i,
                    B_from_last_input_word) in in_B_dsts:
                st_label: Tuple[int, int]
                st = sub_states.get(st_label, None)
                if st is None:
                    st = StateTransInfo(st_label, word_bytes, input_cnt)
                    sub_states[st_label] = st
                st.set_output(out_B_i, in_i, in_B_time,
                              in_B_i, B_from_last_input_word)

    # resolve max lookahead for each input
    max_lookahead_for_input: List[int] = [0 for _ in range(input_cnt)]
    for in_i, in_word_dst in enumerate(input_B_dst):
        for in_B_i, in_B_dsts in enumerate(in_word_dst):
            for st_label, in_B_time, out_B_i, _ in in_B_dsts:
                max_lookahead_for_input[in_i] = max(
                    max_lookahead_for_input[in_i], in_B_time)

    # build fsm
    state_cnt = input_cnt
    tt = StateTransTable(
        word_bytes, max_lookahead_for_input, state_cnt)
    states_for_relict_processing: List[StateTransInfo] = []
    # for all possible in/out configurations
    for ss in sorted(sub_states.values(), key=lambda x: x.label):
        ss: StateTransInfo
        st_i = ss.get_state_i()
        next_ss = ss.get_next_substate(sub_states)
        if next_ss is None:
            next_st_i = 0
        else:
            next_st_i = next_ss.get_state_i()

        tr = StateTransItem(tt, st_i, next_st_i, int(next_ss is None))
        tt.state_trans[st_i].append(tr)
        o_prev = None
        for last, (out_B_i, o) in iter_with_last(enumerate(ss.outputs)):
            if o is None:
                o_prev = o
                # output byte is disconnected, which is default state
                continue
            # in_i - input stream index
            # in_t - input time (register index)
            (in_i, in_t, in_B_i, is_from_last_input_word) = o
            in_rec: InputRegInputVal = tr.input[in_i][in_t]
            # vld, keep required as we are planing to use this byte in output
            in_rec.keep[in_B_i] = 1
            in_rec.last = is_from_last_input_word
            tr.out_byte_mux_sel[out_B_i] = (in_i, in_t, in_B_i)
            tr.input_rd[in_i] = 1
            # next keep = 0 because this byte will be consumed
            tr.input_keep_mask[in_i][in_t][in_B_i] = 0
            tr.output_keep[out_B_i] = 1

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

            is_first_input_byte = is_from_different_input(o_prev, o)
            # is last byte from input byte in this output word
            is_last_input_byte = is_from_different_input(o, o_next)

            if is_last_input_byte:
                assert not is_input_word_continuing_in_next_out_word
                # iterate for all inputs until next input or end (if there are not any) and
                #     mark its input keep with 0 and last with 1 to mark for 0B frame input
                next_input_i = input_cnt if o_next is None else o_next[0]
                for skiped_input_i in range(in_i + 1, next_input_i):
                    _in_rec: InputRegInputVal = tr.input[skiped_input_i][0]
                    _in_rec.last = 1
                    _in_rec.keep = [0 for _ in _in_rec.keep]
                    _in_rec.relict = 1
                    tr.input_rd[skiped_input_i] = 1
                    tr.input_keep_mask[skiped_input_i][0] = [0 for _ in range(word_bytes)]

                next_input_can_be_zero_len = not is_input_word_continuing_in_next_out_word and\
                                             o_next is not None \
                                             and can_be_zero_len_frame[next_input_i]
                if next_input_can_be_zero_len:
                    # mark that the next_input does not have 0B frame
                    # to distinguish between the transitions which are skipping the input
                    assert o_next is not None
                    (next_in_i, next_in_t, next_in_B_i, _) = o_next
                    next_in_rec: InputRegInputVal = tr.input[next_in_i][next_in_t]
                    # vld, keep required as we are planing to use this byte in output in the future
                    next_in_rec.keep[next_in_B_i] = 1

            if is_first_input_byte:
                if in_B_i != 0:
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
                    # or this may be a last word but it is not fully consumed
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
                # where only part of the word can be consumed to a output word
                v.relict = int(first_input_is_relict)
            break

    if can_be_zero_len_frame[0]:
        # The previous code generates the transition starting
        # from the state corresponding to a minimal index of input used in it and the starting
        # state is 0, thus all cases where some prefix input was 0B frame now starting in non starting state
        prefix_zero_len_inputs_cnt = 0
        for can_0B in can_be_zero_len_frame:
            if can_0B:
                prefix_zero_len_inputs_cnt += 1
            else:
                break

        for orig_st_i in range(1, min(prefix_zero_len_inputs_cnt + 1, input_cnt)):
            for tr in tt.state_trans[orig_st_i]:
                new_tr: StateTransItem = deepcopy(tr)
                new_tr.state = 0
                # wait and consume 0B frames from all inputs where it is expected
                for input_with_0B_i in range(tr.state):
                    in_rec: InputRegInputVal = new_tr.input[input_with_0B_i][0]
                    in_rec.keep = [0 for _ in range(word_bytes)]
                    in_rec.last = 1
                    in_rec.relict = 1
                    new_tr.input_rd[input_with_0B_i] = 1
                    new_tr.input_keep_mask[input_with_0B_i][0] = [0 for _ in range(word_bytes)]

                tt.state_trans[0].append(new_tr)

        if prefix_zero_len_inputs_cnt == input_cnt:
            # everythin can be 0B frame, we need to add a special transition exactly for that
            # because we did not process it by previous code because it looks only on output bytes
            # and there are not output bytes
            tr = StateTransItem(tt, 0, 0, 1)
            tt.state_trans[0].append(tr)
            for in_recs in tr.input:
                in_rec: InputRegInputVal = in_recs[0]
                in_rec.last = 1
                in_rec.keep = [0 for _ in in_rec.keep]
                in_rec.relict = 1

            for skiped_input in tr.input_keep_mask:
                skiped_input[0] = [0 for _ in range(word_bytes)]

            tr.last = 1
            tr.input_rd = [1 for _ in tr.input_rd]

    tt.filter_unique_state_trans()
    tt.assert_transitions_deterministic()
    return tt

