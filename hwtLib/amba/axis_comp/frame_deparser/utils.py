from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwtLib.amba.axis import AxiStream, axis_mask_propagate_best_effort
from hwt.code_utils import connect_optional
from hwt.synthesizer.interface import Interface


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


def connect_optional_with_best_effort_axis_mask_propagation(src, dst):
    def check_fn(a, b):
        if a._name in ("strb", "keep") and isinstance(a._parent, AxiStream):
            # if is srtb/keep we already connected it by 
            # axis_mask_propagate_best_effort
            return False, []

        if isinstance(a, AxiStream):
            res = axis_mask_propagate_best_effort(a, b)
        else:
            res = []

        return True, res

    return connect_optional(src, dst, check_fn)


def drill_down_in_HStruct_fields(t: HdlType, intf: Interface):
    """
    Find a base type and corresponding interface for nested HStruct with a single
    field.
    """
    while isinstance(t, HStruct):
        assert len(t.fields) == 1, t
        f = t.fields[0]
        if f.name is None:
            intf = None
        elif intf is not None:
            intf = getattr(intf, f.name)
        t = f.dtype
    return t, intf