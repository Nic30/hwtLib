from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.synthesizer.interface import Interface
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.frame_deparser.strb_keep_stash import axis_mask_propagate_best_effort
from ipCorePackager.constants import DIRECTION


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



