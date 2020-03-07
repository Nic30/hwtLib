from typing import Union, Tuple, List

from hwt.code import Concat
from hwt.hdl.typeShortcuts import vec
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.hdl.value import Value
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.axis import AxiStream
from ipCorePackager.constants import DIRECTION
from pyMathBitPrecise.bit_utils import mask
from hwt.synthesizer.unit import Unit


def _get_only_stream(t: HdlType):
    """
    Return HStream if base datatype is HStream.
    (HStream field may be nested in HStruct)
    """
    if isinstance(t, HStream):
        return t
    elif isinstance(t, HStruct) and len(t.fields) == 1:
        return _get_only_stream(t.fields[0].dtype)
    return None


def axis_mask_propagate_best_effort(src: AxiStream, dst: AxiStream):
    if src.USE_STRB:
        if not src.USE_KEEP and not dst.USE_STRB and dst.USE_KEEP:
            dst.keep(src.strb)
    if src.USE_KEEP:
        if not src.USE_STRB and not dst.USE_KEEP and dst.USE_STRB:
            dst.strb(src.keep)
    if not src.USE_KEEP and not src.USE_STRB:
        if dst.USE_KEEP:
            dst.keep(mask(dst.keep._dtype.bit_length()))
        if dst.USE_STRB:
            dst.strb(mask(dst.strb._dtype.bit_length()))


def _connect_if_present_on_dst(src: Interface, dst: Interface,
                               dir_reverse=False, connect_keep_to_strb=False):
    if not src._interfaces:
        assert not dst._interfaces, (src, dst)
        if dir_reverse:
            src(dst)
        else:
            dst(src)
    for _s in src._interfaces:
        _d = getattr(dst, _s._name, None)
        if _d is None:
            continue
        if _d._masterDir == DIRECTION.IN:
            rev = not dir_reverse
        else:
            rev = dir_reverse

        _connect_if_present_on_dst(_s, _d, dir_reverse=rev,
                                   connect_keep_to_strb=connect_keep_to_strb)
        if _s._name == "strb" and connect_keep_to_strb:
            _connect_if_present_on_dst(_s, dst.keep, dir_reverse=rev,
                                       connect_keep_to_strb=connect_keep_to_strb)
    if isinstance(src, AxiStream):
        axis_mask_propagate_best_effort(src, dst)


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
        if not isinstance(strb, Value) or strb != STRB_ALL:
            extra_strbs.append((inversedWordIndex, strb))

        keep = self._vec_to_signal(self.keep)
        if not isinstance(keep, Value) or keep != STRB_ALL:
            extra_keeps.append((inversedWordIndex, keep))


def reduce_conditional_StrbKeepStashes(parent: Unit, sk_stashes: List[StrbKeepStash], STRB_ALL: int):
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

