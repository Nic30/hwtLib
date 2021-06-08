from typing import Dict, List, Optional


class InputRegInputVal():
    """
    Container of values for FrameJoin input register

    :ivar ~.parent: the StateTransItem instance which is owning this object
    :ivar ~.keep: list of keep bits
    :ivar ~.relict: flag for word which was partially consumed
    :ivar ~.last: flag for end of frame
    """

    def __init__(self, parent_state_trans: "StateTransItem"):
        self.parent = parent_state_trans
        self.keep: List[Optional[int]] = [None for _ in range(parent_state_trans.parent.word_bytes)]
        self.relict: Optional[int] = None
        self.last: Optional[int] = None

    def as_tuple(self):
        return (tuple(self.keep), self.relict, self.last)

    def is_exactly_different(self, other):
        assert len(self.keep) == len(other.keep)
        for k0, k1 in zip(self.keep, other.keep):
            if k0 is None or k1 is None:
                continue
            if k0 != k1:
                return True
        if self.last is not None and other.last is not None\
                and self.last != other.last:
            return True

        return self.relict is not None and other.relict is not None\
            and self.relict != other.relict

    @classmethod
    def from_dict(cls, parent_state_trans, d: Dict):
        self = cls(parent_state_trans)
        self.keep = val_replace_X_with_None(d['keep'])
        self.relict = val_replace_X_with_None(d['relict'])
        self.last = val_replace_X_with_None(d['last'])
        return self

    def __repr__(self):
        return "{'keep':%s, 'relict':%s, 'last':%s}" % (
            val__repr__None_as_X(self.keep),
            val__repr__None_as_X(self.relict),
            val__repr__None_as_X(self.last)
        )


def val_replace_X_with_None(v):
    if isinstance(v, str) and v == 'X':
        return None
    elif isinstance(v, list):
        return [val_replace_X_with_None(x) for x in v]
    else:
        return v


def val__repr__None_as_X(v):
    if v is None:
        return "'X'"
    elif isinstance(v, int):
        return '%d' % v
    else:
        b = []
        for v1 in v:
            b.append(val__repr__None_as_X(v1))
        return "[%s]" % ", ".join(b)
