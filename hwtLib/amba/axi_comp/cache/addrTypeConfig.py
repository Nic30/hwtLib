from typing import Tuple

from hwt.code import Concat
from hwt.hdl.types.bits import Bits
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from pyMathBitPrecise.bit_utils import mask


class CacheAddrTypeConfig(Unit):
    """
    A container of address type configuration
    and address parsing utils.

    :ivar ADDR_WIDTH: the total width of the address in bits
    :ivar CACHE_LINE_SIZE: cache line width in bytes
    :ivar CACHE_LINE_CNT: total number of cache lines
        available in this cache (sum in all sets/"ways" together).

    Address is composed of several parts as shown in table bellow:

        +-------+--------+--------+
        |  tag  |  index | offset |
        +-------+--------+--------+

    * offset is an offset in cacheline
    * index is an index of set where the cacheline could be stored in cache
    * tag is a rest of address used to check if the calenine stored on index in cache is the cacheline
      of the requested address
    """

    def _config(self):
        if not hasattr(self, "ADDR_WIDTH"):
            self.ADDR_WIDTH = Param(32)
        self.CACHE_LINE_SIZE = Param(64)
        self.CACHE_LINE_CNT = Param(4096)

    def _compupte_tag_index_offset_widths(self):
        self.OFFSET_W = log2ceil(self.CACHE_LINE_SIZE - 1)
        self.INDEX_W = log2ceil(self.CACHE_LINE_CNT // self.WAY_CNT - 1)
        self.TAG_W = self.ADDR_WIDTH - self.INDEX_W - self.OFFSET_W

    def parse_addr_int(self, addr: int) -> Tuple[int, int, int]:
        tag = addr >> (self.INDEX_W + self.OFFSET_W)
        index = (addr >> self.OFFSET_W) & mask(self.INDEX_W)
        offset = addr & mask(self.OFFSET_W)
        return tag, index, offset

    def parse_addr(self, addr) -> Tuple[RtlSignal, RtlSignal, RtlSignal]:
        tag = addr[:(self.INDEX_W + self.OFFSET_W)]
        index = addr[(self.INDEX_W + self.OFFSET_W):self.OFFSET_W]
        offset = addr[self.OFFSET_W:]
        return tag, index, offset

    def addr_in_data_array(self, way: RtlSignal, index: RtlSignal):
        return Concat(way, index)

    def deparse_addr(self, tag, index, offset) -> Tuple[RtlSignal, RtlSignal, RtlSignal]:
        assert tag._dtype.bit_length() == self.TAG_W, (tag._dtype, self.TAG_W)
        if isinstance(offset, int):
            offset = Bits(self.OFFSET_W).from_py(offset)
        else:
            assert offset._dtype.bit_length() == self.OFFSET_W, (self.OFFSET_W, offset._dtype)

        if isinstance(index, int):
            index = Bits(self.INDEX_W).from_py(index)
        else:
            assert index._dtype.bit_length() == self.INDEX_W, (self.INDEX_W, index._dtype)

        return Concat(tag, index, offset)
