from itertools import islice
from typing import List

from hwt.math import log2ceil


class StateTransTable():

    def __init__(self, word_bytes: int,
                 max_lookahead_for_input: List[int],
                 state_cnt: int):
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

    def assert_transitions_deterministic(self):
        for st_trans in self.state_trans:
            for i, t0 in enumerate(st_trans):
                # assert each other transition difers at least in a single value for any input
                # :note: None notes undefined value
                for t1 in islice(st_trans, i + 1, None):
                    if not t0.inputs_exactly_different(t1):
                        raise AssertionError("non-deterministic state transition", t0, t1)

    def filter_unique_state_trans(self):
        self.state_trans = [sorted(set(t)) for t in self.state_trans]
