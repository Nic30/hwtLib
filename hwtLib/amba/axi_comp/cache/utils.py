from math import ceil

from hwt.code import Concat
from hwt.math import log2ceil
from hwtLib.amba.axi_comp.lsu.interfaces import AddrDataIntf
from hwtLib.mem.cam import CamMultiPort
from pyMathBitPrecise.bit_utils import apply_set_and_clear
from hwt.hdl.types.bits import Bits


def expand_byte_mask_to_bit_mask(m):
    res = []
    for b in m:
        B = []
        for _ in range(8):
            B.append(b)

        res.append(Concat(*B))

    return Concat(*reversed(res))


def apply_write_with_mask(current_data, new_data, write_mask):
    m = expand_byte_mask_to_bit_mask(write_mask)
    return apply_set_and_clear(current_data, new_data & m, m)


def extend_to_width_multiple_of_8(sig):
    """
    make width of signal modulo 8 equal to 0
    """
    w = sig._dtype.bit_length()
    cosest_multiple_of_8 = ceil((w // 8) / 8) * 8
    if cosest_multiple_of_8 == w:
        return sig
    else:
        return Concat(Bits(cosest_multiple_of_8 - w).from_py(0), sig)


class CamWithReadPort(CamMultiPort):
    """
    Content addressable memory with a read port which can be used
    to read cam array by index

    .. hwt-autodoc::
    """

    def _config(self):
        CamMultiPort._config(self)
        self.USE_VLD_BIT = False

    def _declr(self):
        assert not self.USE_VLD_BIT
        CamMultiPort._declr(self)
        r = self.read = AddrDataIntf()
        r.ADDR_WIDTH = log2ceil(self.ITEMS - 1)
        r.DATA_WIDTH = self.KEY_WIDTH

    def _impl(self):
        CamMultiPort._impl(self)
        self.read.data(self._mem[self.read.addr])

