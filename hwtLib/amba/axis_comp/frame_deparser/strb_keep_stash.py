from typing import Union, Tuple, List

from hwt.code import Concat
from hwt.hdl.typeShortcuts import vec
from hwt.hdl.value import HValue
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from pyMathBitPrecise.bit_utils import mask


class StrbKeepStash():
    def __init__(self):
        self.strb = []
        self.keep = []

    def push(self, strb, keep):
        self.strb.append(strb)
        self.keep.append(keep)

    @staticmethod
    def _push_mask_vec(res, data_len, data_valid):
        assert data_len % 8 == 0, "mask generated from padding is byte aligned"
        if isinstance(data_valid, RtlSignal):
            res.append(data_valid)
        else:
            w = data_len // 8
            v = mask(w) if data_valid else 0
            res.append(vec(int(v), w))

    @staticmethod
    def _vec_to_signal(extra_strbs: Union[Tuple[int, bool], RtlSignal]):
        """
        :param extra_strbs: number of bits and padding flag or strb sinal directly
        """
        res = []
        prev_len = 0
        prev_val = None
        for s in extra_strbs:
            if isinstance(s, Tuple):
                if prev_val is None:
                    prev_len, prev_val = s
                    assert prev_len > 0, prev_len
                elif prev_val is s[1]:
                    # try extend
                    prev_len += s[0]
                else:
                    StrbKeepStash._push_mask_vec(res, prev_len, prev_val)
                    prev_len, prev_val = s
            elif isinstance(s, (RtlSignal, Interface)):
                res.append(s)
                prev_len, prev_val = 0, None

        if prev_val is not None:
            StrbKeepStash._push_mask_vec(res, prev_len, prev_val)
        return Concat(*reversed(res))

    def pop(self, inversedWordIndex, extra_strbs, extra_keeps, STRB_ALL):
        strb = self._vec_to_signal(self.strb)
        if not isinstance(strb, HValue) or strb != STRB_ALL:
            extra_strbs.append((inversedWordIndex, strb))

        keep = self._vec_to_signal(self.keep)
        if not isinstance(keep, HValue) or keep != STRB_ALL:
            extra_keeps.append((inversedWordIndex, keep))


def reduce_conditional_StrbKeepStashes(parent: Unit,
                                       sk_stashes: List[StrbKeepStash],
                                       STRB_ALL: int):
    strb_val_to_en = {}
    keep_val_to_en = {}
    for (en, sk) in sk_stashes:
        strb = sk._vec_to_signal(sk.strb)
        keep = sk._vec_to_signal(sk.keep)
        strb_val_to_en.setdefault(strb, []).append(en)
        keep_val_to_en.setdefault(keep, []).append(en)

    if len(strb_val_to_en) == 1:
        strb = strb_val_to_en.popitem()
    else:
        raise NotImplementedError()

    if len(keep_val_to_en) == 1:
        keep = keep_val_to_en.popitem()
    else:
        raise NotImplementedError()

    return strb, keep
