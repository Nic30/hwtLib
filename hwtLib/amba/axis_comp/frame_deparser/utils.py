from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwtLib.amba.axi4s import Axi4Stream, axi4s_mask_propagate_best_effort
from hwt.code_utils import connect_optional
from hwt.hwIO import HwIO


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
        if a._name in ("strb", "keep") and isinstance(a._parent, Axi4Stream):
            # if is srtb/keep we already connected it by 
            # axi4s_mask_propagate_best_effort
            return False, []

        if isinstance(a, Axi4Stream):
            res = axi4s_mask_propagate_best_effort(a, b)
        else:
            res = []

        return True, res

    return connect_optional(src, dst, check_fn)


def drill_down_in_HStruct_fields(t: HdlType, hwIO: HwIO):
    """
    Find a base type and corresponding interface for nested HStruct with a single
    field.
    """
    while isinstance(t, HStruct):
        assert len(t.fields) == 1, t
        f = t.fields[0]
        if f.name is None:
            hwIO = None
        elif hwIO is not None:
            hwIO = getattr(hwIO, f.name)
        t = f.dtype
    return t, hwIO