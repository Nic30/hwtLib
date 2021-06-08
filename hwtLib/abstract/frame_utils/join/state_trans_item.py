from copy import deepcopy
from typing import Dict, List, Optional

from hwtLib.abstract.frame_utils.join.input_reg_val import InputRegInputVal
from hwtLib.abstract.frame_utils.join.state_trans_table import StateTransTable


def _cmp_with_None_as_2(o0, o1):
    """
    :return: 0 if o0 == o1, -1 if o0 < o1, 1 if o0 > o1
    """
    if isinstance(o1, tuple):
        assert len(o0) == len(o1), (o0, o1)
        for _o0, _o1 in zip(o0, o1):
            cmp = _cmp_with_None_as_2(_o0, _o1)
            if cmp != 0:
                return cmp

        return 0

    else:
        if o0 is None:
            o0 = 2
        if o1 is None:
            o1 = 2

        if o0 < o1:
            return -1
        elif o0 > o1:
            return 1

        return 0


class StateTransItem():
    """
    :ivar state: state label
    :ivar input: specifies the input to a state transition
    :ivar input_keep_mask: mask which will be applied to keep signal on input to the register
    :note: input_keep_mask[0][0] = [1, 0] means reg0.in.keep = reg0.out.keep & 0b01
    :ivar input_rd: ready for a input channel (if 1 the input stream will be shifted in)
    :ivar output_keep: output keep values
    :ivar out_byte_mux_sel: list of
    """

    def __init__(self, parent_table: StateTransTable, st_i: int, state_next_i: int, out_last: int):
        self.parent = parent_table
        self.state = st_i
        self.input: List[List[InputRegInputVal]] = []
        # for input
        for in_reg_max in parent_table.max_lookahead_for_input:
            # for registers on input
            _input = []
            for _ in range(in_reg_max + 1):
                _input.append(InputRegInputVal(self))
            self.input.append(_input)

        # outputs

        self.input_keep_mask: List[List[List[Optional[int]]]] = [
            [] for _ in range(parent_table.input_cnt)
        ]
        for input_keep_mask, in_reg_max in zip(
                self.input_keep_mask,
                parent_table.max_lookahead_for_input):
            for _ in range(in_reg_max + 1):
                input_keep_mask.append(
                    [1 for _ in range(parent_table.word_bytes)])
        self.input_rd: List[Optional[int]] = [0 for _ in range(parent_table.input_cnt)]
        self.output_keep: List[Optional[int]] = [0 for _ in range(parent_table.word_bytes)]
        self.out_byte_mux_sel: List[Optional[int]] = [None for _ in range(parent_table.word_bytes)]
        self.state_next = state_next_i
        self.last = out_last

    def as_tuple(self):
        t = (
            self.state,
            self.state_next,
            tuple(tuple(i2.as_tuple()
                        for i2 in i)
                  for i in self.input),
            tuple(tuple(tuple(i2)
                        for i2 in i)
                  for i in self.input_keep_mask),
            tuple(self.input_rd),
            tuple(self.output_keep),
            tuple(self.out_byte_mux_sel),
            self.last,
        )
        return t

    def __lt__(self, other):
        return _cmp_with_None_as_2(self.as_tuple(), other.as_tuple()) < 0

    def __eq__(self, other):
        return self is other or self.as_tuple() == other.as_tuple()

    def inputs_exactly_different(self, other: "StateTransItem") -> bool:
        assert len(self.input) == len(other.input), (self, other)
        for in_regs0, in_regs1 in zip(self.input, other.input):
            assert len(in_regs0) == len(in_regs1), (self, other)
            for in0, in1 in zip(in_regs0, in_regs1):
                if in0.is_exactly_different(in1):
                    return True
        return False

    def __hash__(self):
        return hash(self.as_tuple())

    def __deepcopy__(self, memo):
        """
        Deepcopy, but do not copy the parent
        """
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == "parent":
                new_v = v
            else:
                new_v = deepcopy(v, memo)
            setattr(result, k, new_v)

        return result

    @classmethod
    def from_dict(cls, parent, d: Dict):
        st, st_next = d["st"].split("->")
        self = cls(parent, int(st), int(st_next), d["out.last"])
        self.input = [
            [InputRegInputVal.from_dict(self, iriv) for iriv in _in]
            for _in in d["in"]
        ]
        self.input_keep_mask = d["in.keep_mask"]
        self.input_rd = d["in.rd"]
        self.output_keep = d["out.keep"]
        self.out_byte_mux_sel = d["out.mux"]
        return self

    def __repr__(self, as_dict=False):
        if as_dict:
            header = "{"
            footer = "}"
        else:
            header = f"<{self.__class__.__name__} "
            footer = ">"
        return ("%s'st':'%r->%r', 'in':%r, \n"
                "    'in.keep_mask':%r, 'in.rd':%r,\n"
                "    'out.keep':%r, 'out.mux':%r, 'out.last':%r%s") % (
            header,
            self.state, self.state_next, self.input, self.input_keep_mask,
            self.input_rd, self.output_keep, self.out_byte_mux_sel, self.last,
            footer
        )
