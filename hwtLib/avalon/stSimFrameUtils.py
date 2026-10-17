from typing import Union, Sequence, Generator, Deque, Self, Optional, Callable, \
    Any

from hdlConvertorAst.to.hdlUtils import iter_with_last
from hwt.code import Concat
from hwt.constants import NOT_SPECIFIED
from hwt.hdl.const import HConst
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.hdlType import HdlType
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.abstract.simFrameUtils import SimFrameUtils
from hwtLib.avalon.st import AvalonST, AvalonSTAgentWordType
from pyMathBitPrecise.bit_utils import get_bit_range


class AvalonStSimFrameUtils(SimFrameUtils[AvalonSTAgentWordType]):
    """
    Implementation of SimFrameUtils for AvalonST interface.
    """

    def __init__(self, SEGMENT_DATA_WIDTH:int, USE_EMPTY: bool, BYTE_WIDTH:int=8, SEGMENT_CNT:int=1,
                 SUPPORT_ZLP:bool=False, USER_T: Optional[HdlType]=None, USE_SOF:bool=True, ERROR_WIDTH:int=0):
        assert SEGMENT_CNT >= 1, self.SEGMENT_CNT
        self.SEGMENT_CNT = SEGMENT_CNT
        if SEGMENT_CNT > 1:
            raise NotImplementedError()
        self.BYTE_WIDTH = BYTE_WIDTH
        self.SEGMENT_DATA_WIDTH = SEGMENT_DATA_WIDTH
        self.SEGMENT_BYTE_CNT = SEGMENT_DATA_WIDTH // BYTE_WIDTH
        assert SEGMENT_DATA_WIDTH % BYTE_WIDTH == 0
        self.SUPPORT_ZLP = SUPPORT_ZLP
        self.USE_SOF = USE_SOF
        self.ERROR_WIDTH = ERROR_WIDTH
        self.USE_EMPTY = USE_EMPTY
        self.USER_T = USER_T
        self._WORD_MEMBER_CASTS = self._getWordMemberCasts()
    
    def _getWordMemberCasts(self) -> tuple[Optional[Callable[[Any], HBitsConst]], ...]:
        res: list[Optional[Callable[[Any], HBitsConst]]] = [
            None,  # data
        ]
        # data, empty?, error?, user?, sof?, eof 
        if self.USE_EMPTY:
            emptyT = HBits(AvalonST._getWidthOfEmpty(self.SEGMENT_DATA_WIDTH, self.BYTE_WIDTH, self.SUPPORT_ZLP)).from_py        
            res.append(emptyT)
        ERROR_WIDTH = self.ERROR_WIDTH
        if ERROR_WIDTH:
            errorT = HBits(ERROR_WIDTH).from_py
            res.append(errorT)
        USER_T = self.USER_T
        if USER_T is not None:
            res.append(USER_T.from_py)
        if self.USE_SOF:
            res.append(BIT.from_py)
        res.append(BIT.from_py)  # eof
        return res
    
    @override
    @classmethod
    def from_HwIO(cls, hwio: AvalonST) -> Self:
        return cls(hwio.DATA_WIDTH,
                   hwio.USE_EMPTY,
                   SEGMENT_CNT=hwio.packetsPerClock,
                   BYTE_WIDTH=hwio.dataBitsPerSymbol,
                   SUPPORT_ZLP=hwio.SUPPORT_ZLP,
                   USER_T=hwio.USER_T,
                   USE_SOF=True,
                   ERROR_WIDTH=hwio.ERROR_WIDTH)

    @override
    def pack_frame(self, frameVal: Union[HConst, Sequence[int]], userFirstWord=NOT_SPECIFIED)\
            ->Generator[AvalonSTAgentWordType, None, None]:
        frameVal, frameIsZeroLen = self._toHConst(frameVal)

        byte_cnt = self.SEGMENT_BYTE_CNT
        USE_SOF = self.USE_SOF
        USE_EMPTY = self.USE_EMPTY
        ERROR_WIDTH = self.ERROR_WIDTH
        USE_USER = self.USER_T
        if USE_USER is None:
            assert userFirstWord is NOT_SPECIFIED

        if frameIsZeroLen:
            word = [None  # data
                    ]
            if USE_EMPTY:
                word.append(byte_cnt)
            if ERROR_WIDTH:
                word.append(0)
            if USE_USER is not None:
                word.append(userFirstWord)
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
            if USE_USER is not None:
                word.append(userFirstWord if first else None)
            if USE_SOF:
                word.append(first)

            word.append(last)  # eof

            yield tuple(word)
            if first:
                first = False

    @override
    def concatWordBits(self, frameBeats: Sequence[AvalonSTAgentWordType]):
        WORD_MEMBER_CASTS = self._WORD_MEMBER_CASTS
        memberCnt = len(WORD_MEMBER_CASTS)
        for busWord in frameBeats:
            # :note: data on lower bits, eof at msb
            assert len(busWord) == memberCnt
            yield Concat(*reversed(d if cast is None else cast(d) for cast, d in zip(WORD_MEMBER_CASTS, busWord)))

    @override
    def updackWordBits(self, v: HBitsConst):
        # data, empty?, error?, user?, sof?, eof 
        d = [
            v[self.DATA_WIDTH:],  # data
        ]
        off = self.DATA_WIDTH
        if self.USE_EMPTY:
            emptyW = AvalonST._getWidthOfEmpty(self.DATA_WIDTH, self.BYTE_WIDTH, self.SUPPORT_ZLP)
            d.append(v[emptyW + off:off])
            off += emptyW
        ERROR_WIDTH = self.ERROR_WIDTH
        if ERROR_WIDTH:
            d.append(v[ERROR_WIDTH + off:off])
            off += ERROR_WIDTH
        USER_T = self.USER_T
        if USER_T is not None:
            userW = USER_T.bit_length()
            d.append(v[userW + off:off])
            off += userW 
        if self.USE_SOF:
            d.append(v[1 + off:off])
            off += 1 
        d.append(v[1 + off:off])  # eof
        assert v._dtype.bit_length() == off + 1, ("word value should not contain any additional bits", (v._dtype.bit_length(), off + 1))
        return tuple(d)

    @override
    def receive_bytes(self, ag_data:Deque[AvalonSTAgentWordType]) -> tuple[int, list[Union[int, HBitsConst]], bool]:
        data_B: list[int] = []
        eof = False
        err = 0
        user = None
        first = True
        SEGMENT_BYTE_CNT = self.SEGMENT_BYTE_CNT
        USE_SOF = self.USE_SOF
        ERROR_WIDTH = self.ERROR_WIDTH
        USE_EMPTY = self.USE_EMPTY
        wordMemberCnt = len(self._WORD_MEMBER_CASTS)
        USE_USER = self.USER_T
        firstWordUser = NOT_SPECIFIED
        
        while ag_data:
            _d = ag_data.popleft()
            assert len(_d) == wordMemberCnt, (len(_d), wordMemberCnt)
            dIt = iter(_d)
            data = next(dIt)
            if USE_EMPTY:
                empty = next(dIt)
            else:
                empty = 0
            if ERROR_WIDTH:
                err = next(dIt)
            if USE_USER:
                user = next(dIt)
            if USE_SOF:
                sof = next(dIt)
            else:
                sof = not data_B
            eof = next(dIt)
           
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
                        f' based on value of "empty" B_i:{i:d},'
                        f' empty:{empty:d}, vld_mask:0x{data.vld_mask:x}')
                data_B.append(d)
            
            if sof:
                firstWordUser = user
            
            if first:
                first = False

            if eof:
                break

        if not eof:
            if data_B:
                raise ValueError("Unfinished frame", data_B)
            else:
                raise ValueError("No frame available")

        return 0, data_B, err, firstWordUser

