
class StateTransInfo():
    """
    :ivar ~.label: tuple(frame id, word id)
    :ivar ~.outputs: list of tuples (input index, input time, input byte index)
    :type outputs: List[Optional[Tuple[int, int, int]]]
    :ivar ~.last_per_input: last flags for each input if last=1
        the the input word is end of the actual frame
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
        return "<%s %s o:%r>" % (self.__class__.__name__,
                                 self.label, self.outputs)

