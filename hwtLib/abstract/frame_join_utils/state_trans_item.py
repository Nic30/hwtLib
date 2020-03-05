from hwtLib.abstract.frame_join_utils.input_reg_val import InputRegInputVal


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
                _input.append(InputRegInputVal(self))
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
