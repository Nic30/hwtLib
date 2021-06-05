from typing import Dict, Tuple, Optional, List


class StateTransInfo():
    """
    :ivar ~.label: tuple(frame id, word id)
    :ivar ~.outputs: list of tuples (input index, input time, input byte index)
    :ivar ~.last_per_input: last flags for each input if last=1
        the the input word is end of the actual frame
        (None = don't care value)
    """

    def __init__(self, label, word_bytes, input_cnt):
        self.label = label
        self.outputs: List[Optional[Tuple[int, int, int]]] = [None for _ in range(word_bytes)]
        self.last_per_input: List[Optional[int]] = [None for _ in range(input_cnt)]

    def get_state_i(self) -> int:
        """
        :return: source state index for this state transition, min input index used when this state transition can happen
        """
        return min([x[0] for x in self.outputs if x is not None])

    def get_next_substate(self, sub_states: Dict[Tuple[int, int], "StateTransInfo"]) -> Optional["StateTransInfo"]:
        return sub_states.get((self.label[0], self.label[1] + 1), None)

    def __eq__(self, other):
        return self.label == other.label

    def set_output(self, out_B_i, in_i, time, in_B_i, B_from_last_input_word):
        v = (in_i, time, in_B_i, B_from_last_input_word)
        assert self.outputs[out_B_i] is None, (
            self, out_B_i, self.outputs[out_B_i], v)
        self.outputs[out_B_i] = v

    def __repr__(self):
        return f"<{self.__class__.__name__:s} {self.label:s} o:{self.outputs}>"

