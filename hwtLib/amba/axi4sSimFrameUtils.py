from typing import Union, Deque, Generator, Sequence

from hwt.code import Concat
from hwt.hdl.const import HConst
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.defs import BIT
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.abstract.simFrameUtils import SimFrameUtils
from hwtLib.amba.axi4s import Axi4Stream, Axi4StreamAgentWordType
from pyMathBitPrecise.bit_utils import mask, get_bit, \
    get_bit_range, set_bit


class Axi4StreamSimFrameUtils(SimFrameUtils[Axi4StreamAgentWordType]):

    def __init__(self, DATA_WIDTH: int, USE_STRB=False, USE_KEEP=False, USE_ID=False, BYTE_WIDTH=8):
        self.DATA_WIDTH = DATA_WIDTH
        self.BYTE_WIDTH = BYTE_WIDTH
        self.BYTE_CNT = DATA_WIDTH // BYTE_WIDTH
        self.USE_STRB = USE_STRB
        self.USE_KEEP = USE_KEEP
        self.USE_ID = USE_ID
        self.maskT = HBits(DATA_WIDTH // self.BYTE_WIDTH)

    @override
    @classmethod
    def from_HwIO(cls, axis: Axi4Stream):
        USE_ID = bool(getattr(axis, "ID_WIDTH", 0))
        if getattr(axis, "USER_WIDTH", 0):
            raise NotImplementedError()

        USE_KEEP = hasattr(axis, "keep")
        USE_STRB = hasattr(axis, "strb")
        if USE_KEEP and USE_STRB:
            raise NotImplementedError()
        return Axi4StreamSimFrameUtils(axis.DATA_WIDTH, USE_STRB=USE_STRB, USE_KEEP=USE_KEEP, USE_ID=USE_ID)

    @override
    def pack_frame(self, frameVal: Union[HConst, Sequence[int]])\
            ->Generator[Axi4StreamAgentWordType, None, None]:
        """
        pack data of structure into words on axis interface
        Words are tuples (data, last) or (data, mask, last) depending on args.
        
        :param frameVal: value to be send, HConst instance or list of int for each byte
        
        :returns: generator of tuples (data, strb, isLast), strb is omitted if withStrb=False
        """
        DATA_WIDTH = self.DATA_WIDTH
        withStrb = self.USE_STRB or self.USE_KEEP
        if self.USE_STRB and  self.USE_KEEP:
            raise NotImplementedError()

        frameVal, frameIsZeroLen = self._toHConst(frameVal)
        if frameIsZeroLen:
            if withStrb:
                yield (None, 0, 1)
            else:
                yield (None, 1)
            return

        if withStrb:
            byte_cnt = DATA_WIDTH // 8

        words = iterBits(frameVal, bitsInOne=DATA_WIDTH,
                         skipPadding=False, fillup=True)
        for last, d in iter_with_last(words):
            assert d._dtype.bit_length() == DATA_WIDTH, d._dtype.bit_length()
            if withStrb:
                word_mask = 0
                for B_i in range(byte_cnt):
                    m = get_bit_range(d.vld_mask, B_i * 8, 8)
                    if m == 0xff:
                        word_mask = set_bit(word_mask, B_i)
                    else:
                        assert m == 0, ("Each byte has to be entirely valid"
                                        " or entirely invalid,"
                                        " because of mask granularity", m)
                yield (d, word_mask, last)
            else:
                yield (d, last)

    @override
    def concatWordBits(self, frameBeats: Sequence[Axi4StreamAgentWordType]):
        maskT = self.maskT
        if self.USE_ID:
            raise NotImplementedError()

        if self.USE_KEEP and self.USE_STRB:
            for data, strb, keep, last in frameBeats:
                yield Concat(BIT.from_py(last), maskT.from_py(strb), maskT.from_py(keep), data)
        elif self.USE_KEEP or self.USE_STRB:
            for data, strb, last in frameBeats:
                yield Concat(BIT.from_py(last), maskT.from_py(strb), data)
        else:
            for data, last in frameBeats:
                yield Concat(BIT.from_py(last), data)

    def updackWordBits(self, v: HBitsConst):
        if self.USE_ID:
            raise NotImplementedError()
        d = [
            v[self.DATA_WIDTH:],  # data
        ]
        off = self.DATA_WIDTH
        if self.USE_STRB:
            d.append(v[self.BYTE_CNT + off:off])
            off += self.BYTE_CNT

        if self.USE_KEEP:
            d.append(v[self.BYTE_CNT + off:off])
            off += self.BYTE_CNT

        d.append(v[off])  # last
        assert v._dtype.bit_length() == off + 1, ("word value should not contain any additional bits", (v._dtype.bit_length(), off + 1))
        return tuple(d)

    @override
    def receive_bytes(self, ag_data: Deque[Axi4StreamAgentWordType]) -> tuple[int, list[int]]:
        """
        :param ag_data: list of axi stream words, number of item in tuple depends on use_keep and use_id
        """
        offset = None
        data_B = []
        last = False
        first = True
        id_ = current_id = 0
        BYTE_CNT = self.BYTE_CNT
        BYTE_WIDTH = self.BYTE_WIDTH
        BYTE_MASK = mask(BYTE_WIDTH)
        mask_all = mask(BYTE_CNT)
        use_id = self.USE_ID
        use_keep = self.USE_KEEP
        use_strb = self.USE_STRB
        while ag_data:
            _d = ag_data.popleft()
            if use_id:
                id_ = _d[0]
                id_ = int(id_)
                _d = _d[1:]

            if use_keep:
                if use_strb:
                    data, strb, keep, last = _d
                    strb = int(strb)
                    keep = int(keep)
                else:
                    data, keep, last = _d
                    strb = mask_all
                    keep = int(keep)
            elif use_strb:
                data, strb, last = _d
                strb = int(strb)
                keep = mask_all
            else:
                data, last = _d
                strb = mask_all
                keep = mask_all

            # assert strb & ~keep == 0
            last = int(last)
            if keep == 0:
                assert not data_B, "Empty word in the middle of the packet"
                assert last, "Empty word at the beginning of the packet"
                offset = 0

            if offset is None:
                # first iteration
                # expecting potential 0s in keep and the rest 1
                m = keep
                for i in range(BYTE_CNT):
                    # i represents number of 0 from te beginning of of the keep
                    # value
                    if m & (1 << i):
                        offset = i
                        break
                assert offset is not None, (strb, keep)

            for i in range(BYTE_CNT):
                if get_bit(keep, i):
                    if get_bit(strb, i):
                        d = get_bit_range(data.val, i * BYTE_WIDTH, BYTE_WIDTH)
                        if get_bit_range(data.vld_mask, i * BYTE_WIDTH, BYTE_WIDTH) != BYTE_MASK:
                            raise AssertionError(
                                "Data not valid but it should be"
                                f" based on strb/keep B_i:{i:d}, 0x{keep:x}, 0x{data.vld_mask:x}")
                    else:
                        if last and get_bit_range(strb, i, BYTE_CNT - i) == 0:
                            # skip invalid suffix bytes in last word
                            break
                        if first and not data_B:
                            # skip prefix of invalid bytes in first word
                            continue
                        d = None
                    data_B.append(d)

            if first:
                offset_mask = mask(offset)
                assert offset_mask & keep & strb == 0, (offset_mask, strb, keep)
                first = False
                current_id = id_
            elif not last:
                assert keep == mask_all, (keep, "Does not support non-full words in the non-last word of the frame")
            if not first:
                assert current_id == id_, ("id changed in frame beats", current_id, "->", id_)
            if last:
                break

        if not last:
            if data_B:
                raise ValueError("Unfinished frame", data_B)
            else:
                raise ValueError("No frame available")

        if use_id:
            return offset, id_, data_B
        else:
            return offset, data_B


def axi4s_receive_bytes(axis: Axi4Stream) -> tuple[int, list[int]]:
    """
    Read data from AXI Stream agent in simulation
    and use keep signal to mask out unused bytes
    """
    ag_data = axis._ag.data
    fu = Axi4StreamSimFrameUtils.from_HwIO(axis)
    return fu.receive_bytes(ag_data)


def axi4s_send_bytes(axis: Axi4Stream, data_B: Union[list[int], bytes], offset=0) -> None:
    """
    :param axis: Axi4Stream master which is driver from the simulation
    :param data_B: bytes to send
    :param offset: number of empty bytes which should be added before data
        in frame (and use keep signal to mark such a bytes)
    """
    if axis.ID_WIDTH:
        raise NotImplementedError()
    if axis.USER_WIDTH:
        raise NotImplementedError()
    if axis.USE_KEEP and axis.USE_STRB:
        raise NotImplementedError()
    fu = Axi4StreamSimFrameUtils.from_HwIO(axis)
    fu.send_bytes(data_B, axis._ag.data, offset=offset)


def axi4s_mask_propagate_best_effort(src: Axi4Stream, dst: Axi4Stream):
    res = []
    if src.USE_STRB:
        if not src.USE_KEEP and not dst.USE_STRB and dst.USE_KEEP:
            res.append(dst.keep(src.strb))
    if src.USE_KEEP:
        if not src.USE_STRB and not dst.USE_KEEP and dst.USE_STRB:
            res.append(dst.strb(src.keep))
    if not src.USE_KEEP and not src.USE_STRB:
        if dst.USE_KEEP:
            res.append(dst.keep(mask(dst.keep._dtype.bit_length())))
        if dst.USE_STRB:
            res.append(dst.strb(mask(dst.strb._dtype.bit_length())))
    return res
