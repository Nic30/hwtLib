

class InputRegInputVal():

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
