from typing import Union, Sequence, Generator, Deque, Self

from hdlConvertorAst.to.hdlUtils import iter_with_last
from hwt.code import Concat
from hwt.hdl.const import HConst
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.defs import BIT
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.abstract.simFrameUtils import SimFrameUtils
from hwtLib.avalon.st import AvalonST, AvalonSTAgentWordType
from pyMathBitPrecise.bit_utils import get_bit_range


class AvalonStFrameUtils(SimFrameUtils[AvalonSTAgentWordType]):
    """
    Implementation of SimFrameUtils for AvalonST interface.
    """

    def __init__(self, SEGMENT_DATA_WIDTH:int, USE_EMPTY: bool, BYTE_WIDTH:int=8, SEGMENT_CNT:int=1,
                 SUPPORT_ZLP:bool=False, USE_SOF:bool=True, ERROR_WIDTH:int=0):
        self.SEGMENT_CNT = SEGMENT_CNT
        self.BYTE_WIDTH = BYTE_WIDTH
        self.SEGMENT_DATA_WIDTH = SEGMENT_DATA_WIDTH
        self.SEGMENT_BYTE_CNT = SEGMENT_DATA_WIDTH // BYTE_WIDTH
        assert SEGMENT_DATA_WIDTH % BYTE_WIDTH == 0
        self.SUPPORT_ZLP = SUPPORT_ZLP
        self.USE_SOF = USE_SOF
        self.ERROR_WIDTH = ERROR_WIDTH
        self.USE_EMPTY = USE_EMPTY

    @override
    @classmethod
    def from_HwIO(cls, hwio: AvalonST) -> Self:
        return cls(hwio.SEGMENT_DATA_WIDTH,
                   hwio.SEGMENT_CNT,
                   hwio.USE_EMPTY,
                   SEGMENT_CNT=hwio.packetsPerClock,
                   BYTE_WIDTH=hwio.dataBitsPerSymbol,
                   SUPPORT_ZLP=hwio.SUPPORT_ZLP,
                   USE_SOF=True,
                   ERROR_WIDTH=hwio.ERROR_WIDTH)

    @override
    def pack_frame(self, frameVal: Union[HConst, Sequence[int]])\
            ->Generator[AvalonSTAgentWordType, None, None]:
        frameVal, frameIsZeroLen = self._toHConst(frameVal)

        byte_cnt = self.SEGMENT_BYTE_CNT
        USE_SOF = self.USE_SOF
        USE_EMPTY = self.USE_EMPTY
        ERROR_WIDTH = self.ERROR_WIDTH
        if frameIsZeroLen:
            word = [None  # data
                    ]
            if USE_EMPTY:
                word.append(byte_cnt)
            if ERROR_WIDTH:
                word.append(0)
            if USE_SOF:
                word.append(1)
            word.append(1)  # eof

            yield tuple(word)
            return

        dataWidth = self.SEGMENT_DATA_WIDTH
        words = iterBits(frameVal, bitsInOne=dataWidth,
                         skipPadding=False, fillup=True)
        first = True
        for last, data in iter_with_last(words):
            assert data._dtype.bit_length() == dataWidth, data._dtype.bit_length()
            word = [data, ]
            if USE_EMPTY:
                if last:
                    leftOverSize = (frameVal._dtype.bit_length() // self.BYTE_WIDTH) % byte_cnt
                    if leftOverSize:
                        empty = byte_cnt - leftOverSize
                    else:
                        empty = 0
                else:
                    empty = 0
                word.append(empty)

            if ERROR_WIDTH:
                word.append(0)
            if USE_SOF:
                word.append(first)

            word.append(last)  # eof

            yield tuple(word)
            if first:
                first = False

    @override
    def concatWordBits(self, frameBeats: Sequence[AvalonSTAgentWordType]):
        USE_SOF = self.USE_SOF
        USE_EMPTY = self.USE_EMPTY
        ERROR_WIDTH = self.ERROR_WIDTH
        if USE_EMPTY:
            emptyT = HBits(AvalonST._getWidthOfEmpty(self.DATA_WIDTH, self.BYTE_WIDTH, self.SUPPORT_ZLP)).from_py
        b = BIT.from_py
        if ERROR_WIDTH:
            errorT = HBits(ERROR_WIDTH).from_py
            if USE_EMPTY:
                if USE_SOF:
                    for data, empty, error, sof, eof in frameBeats:
                        yield Concat(b(eof), b(sof), errorT(error), emptyT(empty), data)
                else:
                    for data, empty, error, eof in frameBeats:
                        yield Concat(b(eof), errorT(error), emptyT(empty), data)
            else:
                if USE_SOF:
                    for data, error, sof, eof in frameBeats:
                        yield Concat(b(eof), b(sof), errorT(error), data)
                else:
                    for data, error, eof in frameBeats:
                        yield Concat(b(eof), errorT(error), data)
        else:
            if USE_EMPTY:
                if USE_SOF:
                    for data, empty, error, sof, eof in frameBeats:
                        yield Concat(b(eof), b(sof), emptyT(empty), data)
                else:
                    for data, empty, eof in frameBeats:
                        yield Concat(b(eof), emptyT(empty), data)
            else:
                if USE_SOF:
                    for data, sof, eof in frameBeats:
                        yield Concat(b(eof), b(sof), data)
                else:
                    for data, eof in frameBeats:
                        yield Concat(b(eof), data)

    @override
    def receive_bytes(self, ag_data:Deque[AvalonSTAgentWordType]) -> tuple[int, list[Union[int, HBitsConst]], bool]:
        data_B = []
        eof = False
        err = 0
        first = True
        SEGMENT_BYTE_CNT = self.SEGMENT_BYTE_CNT
        USE_SOF = self.USE_SOF
        ERROR_WIDTH = self.ERROR_WIDTH
        USE_EMPTY = self.USE_EMPTY

        while ag_data:
            _d = ag_data.popleft()

            if ERROR_WIDTH:
                if USE_EMPTY:
                    if USE_SOF:
                        data, empty, err, sof, eof = _d
                    else:
                        data, empty, err, eof = _d
                        sof = not data_B
                else:
                    empty = 0
                    if USE_SOF:
                        data, err, sof, eof = _d
                    else:
                        data, err, eof = _d
                        sof = not data_B
            else:
                err = 0
                if USE_EMPTY:
                    if USE_SOF:
                        data, empty, sof, eof = _d
                    else:
                        data, empty, eof = _d
                        sof = not data_B
                else:
                    empty = 0
                    if USE_SOF:
                        data, sof, eof = _d
                    else:
                        data, eof = _d
                        sof = not data_B
            if USE_SOF:
                sof = bool(sof)
                assert sof == first, ("Soft must be 1 in the first segment of the frame", sof, first)

            if ERROR_WIDTH:
                err |= int(err)

            eof = bool(eof)

            if USE_EMPTY:
                empty = int(empty)
                if not eof and empty != 0:
                    assert eof, "non-full word in the middle of the packet"

            for i in range(SEGMENT_BYTE_CNT - empty):
                d = get_bit_range(data.val, i * 8, 8)
                if get_bit_range(data.vld_mask, i * 8, 8) != 0xff:
                    raise AssertionError(
                        "Data not valid but it should be"
                        f' based on value of "empty" B_i:{i:d}, empty:{empty:d}, vld_mask:0x{data.vld_mask:x}')
                data_B.append(d)

            if first:
                first = False

            if eof:
                break

        if not eof:
            if data_B:
                raise ValueError("Unfinished frame", data_B)
            else:
                raise ValueError("No frame available")

        return 0, data_B, err

