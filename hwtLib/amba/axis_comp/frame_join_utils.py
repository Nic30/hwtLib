from math import inf
from pprint import pprint
from typing import List, Tuple, Dict

from hwt.code import log2ceil
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwtLib.abstract.streamAlignmentUtils import streams_to_all_possible_frame_formats,\
    resolve_input_bytes_destinations


class StateTransInfo():
    """
    :ivar label: tuple(frame id, word id)
    :ivar outputs: list of tuples (input index, input time, input byte index)
    :type outputs: List[Optional[Tuple[int, int, int]]]
    :ivar last_per_input: last flags for each input if last=1 the the input word is end of the actual frame
        (None = don't care value)
    :type last_per_input: List[Optional[int]]
    """

    def __init__(self, label, word_bytes, input_cnt):
        self.label = label
        self.outputs = [None for _ in range(word_bytes)]
        self.last_per_input = [None for _ in range(input_cnt)]

    def __eq__(self, other):
        return self.label == other.label

    def set_output(self, out_B_i, in_i, time, in_B_i, B_from_last_input_word):
        v = (in_i, time, in_B_i, B_from_last_input_word)
        assert self.outputs[out_B_i] is None, (
            self, out_B_i, self.outputs[out_B_i], v)
        self.outputs[out_B_i] = v

    def __repr__(self):
        #info = []
        # if self.is_initial:
        #    info.append("initial")
        # if self.is_final:
        #    info.append("final")

        # return "<%s %s %s>" % (self.__class__.__name__, self.label, ",
        # ".join(info))
        return "<%s %s o:%r>" % (self.__class__.__name__, self.label, self.outputs)


class InputRegInputs():

    def __init__(self, parent_state_trans):
        self.parent = parent_state_trans
        self.keep = [None for _ in range(parent_state_trans.parent.word_bytes)]
        self.last = None

    def as_tuple(self):
        return (tuple(self.keep), self.last)

    def __repr__(self):
        b = []
        # if any(k is not None for k in self.keep):
        b.append("keep:%s" % val__repr__None_as_X(self.keep))
        # if self.last is not None:
        b.append("last:%s" % val__repr__None_as_X(self.last))
        # if self.vld is not None:
        return "<%s>" % (", ".join(b))


def val__repr__None_as_X(v):
    if v is None:
        return "X"
    elif isinstance(v, int):
        return str(v)
    else:
        b = []
        for v1 in v:
            b.append(val__repr__None_as_X(v1))
        return "[%s]" % ",".join(b)


class StateTransItem():

    def __init__(self, parent_table):
        self.parent = parent_table
        self.state = None
        self.input = []
        # for input
        for in_reg_max in parent_table.max_lookahead_for_input:
            # for registers on input
            _input = []
            for _ in range(in_reg_max + 1):
                _input.append(InputRegInputs(self))
            self.input.append(_input)

        # mask which will be applied to keep signal on input to the register
        # :note: self.input_keep_mask[0][0] = [1, 0] means reg0.in.keep = reg0.out.keep & 0b01
        self.input_keep_mask = [[] for _ in range(parent_table.input_cnt)]
        for input_keep_mask, in_reg_max in zip(
                self.input_keep_mask,
                parent_table.max_lookahead_for_input):
            for _ in range(in_reg_max + 1):
                input_keep_mask.append(
                    [1 for _ in range(parent_table.word_bytes)])

        self.input_rd = [0 for _ in range(parent_table.input_cnt)]
        self.output_keep = [0 for _ in range(parent_table.word_bytes)]
        self.out_byte_mux_sel = [None for _ in range(parent_table.word_bytes)]
        self.state_next = None
        self.last = None

    def as_tuple(self):
        t = (
            self.state,
            tuple(tuple(i2.as_tuple() for i2 in i) for i in self.input),
            tuple(tuple(tuple(i2) for i2 in i) for i in self.input_keep_mask),
            tuple(self.input_rd),
            tuple(self.output_keep),
            tuple(self.out_byte_mux_sel),
            self.last,
            self.state_next,
        )
        return t

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()

    def __hash__(self):
        return hash(self.as_tuple())

    def __repr__(self):
        return "<%s %r->%r, in:%r, in.keep_mask:%r, in.rd:%r, out.keep:%r, out.mux:%r, out.last:%r>" % (
            self.__class__.__name__,
            self.state, self.state_next, self.input, self.input_keep_mask,
            self.input_rd, self.output_keep, self.out_byte_mux_sel, self.last
        )


class StateTransTable():

    def __init__(self, word_bytes: int,
                 max_lookahead_for_input: List[int],
                 state_cnt):
        # List[Tuple[inputs, outputs]]
        input_cnt = len(max_lookahead_for_input)
        self.state_trans = [[] for _ in range(state_cnt)]
        self.input_cnt = input_cnt
        self.max_lookahead_for_input = max_lookahead_for_input
        self.word_bytes = word_bytes
        # keep + last + valid
        self.input_bits_per_input_reg = word_bytes + 1 + 1
        self.state_cnt = state_cnt
        # number of bytes to store state
        self.state_width = log2ceil(state_cnt)

    def filter_unique_state_trans(self):
        self.state_trans = [list(set(t)) for t in self.state_trans]


def get_state_i(sub_state: StateTransInfo):
    """
    :return: min input index used during state
    """
    return min([x[0] for x in sub_state.outputs if x is not None])


def input_word_boundaries(ss: StateTransInfo, word_bytes):
    start = None
    for i, o in enumerate(ss.outputs):
        if start is None:
            start = o
        elif o is None or start[0] != o[0] or start[1] != o[1]:
            in_i, in_t, in_start_offset, _ = start
            in_end = ss.outputs[i - 1][2]
            yield in_i, in_t, (in_start_offset, in_end)
            start = o

    if start is not None:
        in_i, in_t, in_start_offset, _ = start
        if in_start_offset != 0:
            yield in_i, in_t, (in_start_offset, word_bytes - 1)


def get_next_substate(sub_states: Dict[Tuple[int, int], StateTransInfo],
                      ss: StateTransInfo):
    return sub_states.get((ss.label[0], ss.label[1] + 1), None)


def input_B_dst_to_fsm(word_bytes, input_cnt, input_B_dst):
    # label: StateTransInfo
    sub_states = {}
    for in_i, in_word_dst in enumerate(input_B_dst):
        for in_B_i, in_B_dsts in enumerate(in_word_dst):
            for st_label, in_B_time, out_B_i, B_from_last_input_word in in_B_dsts:
                st = sub_states.get(st_label, None)
                if st is None:
                    st = StateTransInfo(st_label, word_bytes, input_cnt)
                    sub_states[st_label] = st
                st.set_output(out_B_i, in_i, in_B_time,
                              in_B_i, B_from_last_input_word)

    max_lookahead_for_input = [0 for _ in range(input_cnt)]
    for in_i, in_word_dst in enumerate(input_B_dst):
        for in_B_i, in_B_dsts in enumerate(in_word_dst):
            for st_label, in_B_time, out_B_i, _ in in_B_dsts:
                max_lookahead_for_input[in_i] = max(
                    max_lookahead_for_input[in_i], in_B_time)

    # print(max_lookahead_for_input)
    # pprint(sub_states)
    state_cnt = input_cnt
    tt = StateTransTable(word_bytes, max_lookahead_for_input,
                         state_cnt)
    for ss in sub_states.values():
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
        tr.last = next_ss is None
        for out_B_i, o in enumerate(ss.outputs):
            if o is None:
                # output byte is disconnected, which is default state
                continue
            (in_i, time, in_B_i, is_from_last_input_word) = o
            in_rec = tr.input[in_i][time]
            # vld, keep required as we are planing to use this byte in output
            in_rec.keep[in_B_i] = 1
            in_rec.last = is_from_last_input_word
            tr.out_byte_mux_sel[out_B_i] = (in_i, time, in_B_i)
            tr.input_rd[in_i] = 1
            # next keep = 0 because this byte was consumed
            try:
                tr.input_keep_mask[in_i][time][in_B_i] = 0
            except Exception as e:
                raise e
            tr.output_keep[out_B_i] = 1

        for in_i, in_t, (in_start_offset, in_end) in input_word_boundaries(
                ss, word_bytes):
            if in_start_offset != 0:
                # mark leading zero
                tr.input[in_i][in_t].keep[in_start_offset - 1] = 0

            if in_end != word_bytes - 1:
                # mark last zero from end
                tr.input[in_i][in_t].keep[in_end + 1] = 0
        # if we are checking the input keep==0 set keep_mask=0 as well
        # (not required, to make clear that the byte will not be used in code)
        for in_meta, in_keep_mask in zip(tr.input, tr.input_keep_mask):
            for in_i, in_inputs in enumerate(in_meta):
                for B_i, k in enumerate(in_inputs.keep):
                    if k is not None and k == 0:
                        in_keep_mask[in_i][B_i] = 0

    tt.filter_unique_state_trans()
    return tt


def main():
    word_bytes = 2
    f_len = (1, inf)
    #s_t0 = HStream(Bits(8), frame_len=f_len, start_offsets=[0, 1])
    s_t1 = HStream(Bits(16), frame_len=f_len)
    t = HStruct(
       # (s_t0, "f0"),
        (s_t1, "f1"),
        #(s_t1, "f2"),
    )
    out_offset = 0
    frames = streams_to_all_possible_frame_formats(t, word_bytes, out_offset)
    # print(frames)
    input_B_dst = resolve_input_bytes_destinations(
        frames, len(t.fields), word_bytes)
    #for i in input_B_dst:
    #    print(i)
    tt = input_B_dst_to_fsm(word_bytes, len(t.fields), input_B_dst)
    pprint(tt.state_trans)
    #build_state_tree(frames, len(t.fields))
    #d0 = create_frame(word_bytes, 0, 1, 0)
    #d1 = create_frame(word_bytes, 1, 4, 0)
    #
    #print(join_streams(2, d0, d1, offset=0))


if __name__ == "__main__":
    main()
