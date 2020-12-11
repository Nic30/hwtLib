
class ByteSrcInfo():
    """
    Container for informations about byte in stream data

    :ivar ~.stream_i: index of stream
    :ivar ~.word_i: index of word in frame
    :ivar ~.byte_i: index of byte in word
    :ivar ~.is_from_last_input_word: true if this byte comes from
        last word in input frame
    """

    def __init__(self, stream_i: int, word_i: int, byte_i: int,
                 is_from_last_input_word: bool):
        self.stream_i = stream_i
        self.word_i = word_i
        self.byte_i = byte_i
        self.is_from_last_input_word = is_from_last_input_word

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
            and self.as_tuple() == other.as_tuple()

    def __lt__(self, other):
        if other is None:
            return False
        return self.as_tuple() < other.as_tuple()

    def __hash__(self):
        return hash(self.as_tuple())

    def as_tuple(self):
        return (self.stream_i, self.word_i,
                self.byte_i, self.is_from_last_input_word)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__:s} {self.stream_i:d}, w:{self.word_i:d},"
            f" B:{self.byte_i:d}, l:{self.is_from_last_input_word:d}>"
        )
