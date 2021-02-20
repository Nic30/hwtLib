from typing import Union, Tuple, List, Dict

from pyMathBitPrecise.bit_utils import mask

from hwt.code import Concat, Or
from hwt.hdl.types.bitsVal import BitsVal
from hwt.hdl.value import HValue
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.hdl.types.bits import Bits


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
        assert data_len > 0, data_len
        if isinstance(data_valid, tuple):
            m, ens = data_valid
            data_valid = Or(*ens)._ternary(m, Bits(m._dtype.bit_length()).from_py(0))

        if isinstance(data_valid, RtlSignal):
            res.append(data_valid)
        else:
            assert isinstance(data_valid, (int, BitsVal)), data_valid
            w = data_len // 8
            v = mask(w) if data_valid else 0
            res.append(Bits(w).from_py(v))

    @staticmethod
    def _vec_to_signal(extra_strbs: Union[Tuple[int, bool], RtlSignal]):
        """
        :param extra_strbs: number of bits and padding flag or strb signal directly
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


#def reduce_conditional_StrbKeepStashes(sk_stashes: List[StrbKeepStash]):
#    strb_chunks = []
#    keep_chunks = []
#    for (en, sk) in sk_stashes:
#        strb = sk._vec_to_signal(sk.strb)
#        keep = sk._vec_to_signal(sk.keep)
#        strb_chunks.append(en._ternary(strb, strb._dtype.from_py(0)))
#        keep_chunks.append(en._ternary(keep, keep._dtype.from_py(0)))
#
#    return Concat(*reversed(strb_chunks)), Concat(*reversed(keep_chunks))

def pop_mask_value(mask_val_to_en_dict: Dict[HValue, List[RtlSignal]]):
    if len(mask_val_to_en_dict) == 1:
        v, _ = mask_val_to_en_dict.popitem()
        # there is only a single possible value, that means that the decision to a different mask
        # can be done on top level, but on this level the selection signals does not matter
        return v
        # return Or(*ens)._ternary(v, v._dtype.from_py(0))
    else:
        assert mask_val_to_en_dict
        masks = sorted(mask_val_to_en_dict.items(), key=lambda x: x[0])
        m = masks[0][0]._dtype.from_py(0)
        for v, ens in masks:
            assert ens, ens
            m = Or(*ens)._ternary(v, m)
        return m

def reduce_conditional_StrbKeepStashes(sk_stashes: List[StrbKeepStash]):
    strb_val_to_en = {}
    keep_val_to_en = {}
    for (en, sk) in sk_stashes:
        strb = sk._vec_to_signal(sk.strb)
        keep = sk._vec_to_signal(sk.keep)
        strb_val_to_en.setdefault(strb, []).append(en)
        keep_val_to_en.setdefault(keep, []).append(en)

    strb = pop_mask_value(strb_val_to_en)
    strb = pop_mask_value(keep_val_to_en)

    return strb, keep
