from typing import Union, Sequence, Generator, Deque, Self

from hdlConvertorAst.to.hdlUtils import iter_with_last
from hwt.code import Concat
from hwt.hdl.const import HConst
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.struct import HStruct
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.abstract.simFrameUtils import SimFrameUtils
from hwtLib.amba.axi4SSegmented import Axi4StreamSegmented, \
    _Axi4StreamSegmentedWord, Axi4StreamSegmentedAgentWordType
from hwtLib.types.ctypes import uint8_t
from pyMathBitPrecise.bit_utils import get_bit_range


class Axi4StreamSegmentedFrameUtils(SimFrameUtils[Axi4StreamSegmentedAgentWordType]):

    def __init__(self, SEGMENT_DATA_WIDTH:int, SEGMENT_CNT:int, USER_SEGMENT_T: HStruct, BYTE_WIDTH:int=8,
                 SUPPORT_ZLP:bool=False, USE_SOF:bool=False, ERROR_WIDTH:int=0, PACK_SEGMENT_BITS:bool=False):
        self.SEGMENT_CNT = SEGMENT_CNT
        self.BYTE_WIDTH = BYTE_WIDTH
        self.SEGMENT_DATA_WIDTH = SEGMENT_DATA_WIDTH
        self.SEGMENT_BYTE_CNT = SEGMENT_DATA_WIDTH // BYTE_WIDTH
        assert SEGMENT_DATA_WIDTH % BYTE_WIDTH == 0
        self.USER_SEGMENT_T = USER_SEGMENT_T
        self.SUPPORT_ZLP = SUPPORT_ZLP
        self.USE_SOF = USE_SOF
        self.ERROR_WIDTH = ERROR_WIDTH
        self.PACK_SEGMENT_BITS = PACK_SEGMENT_BITS
        self.USE_EMPTY = Axi4StreamSegmented._hasEmpty(SEGMENT_DATA_WIDTH, BYTE_WIDTH, SUPPORT_ZLP)
        self.USE_ENABLE = Axi4StreamSegmented._hasEnable(SEGMENT_CNT)

    @override
    @classmethod
    def from_HwIO(cls, axiss: Axi4StreamSegmented) -> Self:
        return cls(axiss.SEGMENT_DATA_WIDTH,
                   axiss.SEGMENT_CNT,
                   axiss.USER_SEGMENT_T,
                   SUPPORT_ZLP=axiss.SUPPORT_ZLP,
                   USE_SOF=axiss.USE_SOF,
                   ERROR_WIDTH=axiss.ERROR_WIDTH,
                   PACK_SEGMENT_BITS=axiss.PACK_SEGMENT_BITS)

    @override
    def pack_frame(self, frameVal: Union[HConst, Sequence[int]])\
            ->Generator[Axi4StreamSegmentedAgentWordType, None, None]:
        """
        pack data of structure into words on Axi4StreamSegmented interface
        
        :param frameVal: value to be send, HConst instance or list of int for each byte
        
        :returns: generator of tuples tuples (data, USER_SEGMENT_T)
        """
        frameVal, frameIsZeroLen = self._toHConst(frameVal)
        byte_cnt = self.SEGMENT_BYTE_CNT
        USER_SEGMENT_T = self.USER_SEGMENT_T
        USE_SOF = self.USE_SOF
        USE_ENABLE = self.USE_ENABLE
        USE_EMPTY = self.USE_EMPTY
        ERROR_WIDTH = self.ERROR_WIDTH
        if frameIsZeroLen:
            userData = {"eof": 1}
            if USE_ENABLE:
                userData["enable"] = 1
            if USE_EMPTY:
                userData["empty"] = byte_cnt
            if USE_SOF:
                userData["sof"] = 1
            if ERROR_WIDTH:
                userData["err"] = 0

            yield (None, USER_SEGMENT_T.from_py(userData))
            return

        dataWidth = self.SEGMENT_DATA_WIDTH
        words = iterBits(frameVal, bitsInOne=dataWidth,
                         skipPadding=False, fillup=True)
        first = True
        for last, data in iter_with_last(words):
            assert data._dtype.bit_length() == dataWidth, data._dtype.bit_length()
            sof = first
            if first:
                first = False
            eof = last

            userData = {"eof":eof}
            if USE_ENABLE:
                userData["enable"] = 1
            if USE_EMPTY:
                if last:
                    leftOverSize = (frameVal._dtype.bit_length() // self.BYTE_WIDTH) % byte_cnt
                    if leftOverSize:
                        empty = byte_cnt - leftOverSize
                    else:
                        empty = 0
                else:
                    empty = 0
                userData["empty"] = empty

            if USE_SOF:
                userData["sof"] = sof

            if ERROR_WIDTH:
                userData["err"] = 0

            yield (data, USER_SEGMENT_T.from_py(userData))

    @override
    def concatWordBits(self, frameBeats: Sequence[Axi4StreamSegmentedAgentWordType]):
        for segments in frameBeats:
            # in lowest bits first format
            assert segments
            word: list[HBitsConst] = []
            fillerSegmentCnt = self.SEGMENT_CNT - len(segments)
            for data, _ in segments:
                word.append(data)
            for _ in range(fillerSegmentCnt):
                word.append(data._dtype.from_py(None))

            for data, user in segments:
                for f in user._dtype.fields:
                    word.append(getattr(user, f.name))
            
            for _ in range(fillerSegmentCnt):
                for f in user._dtype.fields:
                    if f.name == "enable":
                        word.append(f.dtype.from_py(0))
                    else:
                        word.append(f.dtype.from_py(None))

            yield Concat(*reversed(word))

    @override
    def send_bytes(self, data_B:Union[bytes, list[int]], ag_data:Deque[Axi4StreamSegmentedAgentWordType], offset:int=0) -> list[Axi4StreamSegmentedAgentWordType]:
        if data_B:
            if isinstance(data_B, bytes):
                data_B = [int(x) for x in data_B]
            t = uint8_t[len(data_B) + offset]
            _data_B = t.from_py([None for _ in range(offset)] + data_B)
        else:
            assert self.SUPPORT_ZLP
            _data_B = data_B

        f = self.pack_frame(_data_B)
        SEGMENT_CNT = self.SEGMENT_CNT
        if ag_data:
            # possibly fill unused segments into existing last word
            lastWord = ag_data[-1]
            if len(lastWord) < SEGMENT_CNT:
                newSegmentsForLastWord = []
                for _ in range(SEGMENT_CNT - len(lastWord)):
                    try:
                        newSegmentsForLastWord.append(next(f))
                    except StopIteration:
                        break
                ag_data[-1] = tuple((*lastWord, *newSegmentsForLastWord))

        eof = False
        while not eof:
            segments = []
            for _ in range(SEGMENT_CNT):
                try:
                    seg = next(f)
                    segments.append(seg)
                except StopIteration:
                    eof = True
                    break
                if segments:
                    ag_data.append(tuple(segments))

    @override
    def receive_bytes(self, ag_data:Deque[Axi4StreamSegmentedAgentWordType]) -> tuple[int, list[Union[int, HBitsConst]], bool]:
        """
        :param ag_data: list of axi stream segmented words, number of item in tuple depends on use_keep and use_id
        :returns: tuple (startSegmentIndex, data bytes, had error flag)
        """
        data_B = []
        sof = True
        eof = False
        err = 0
        first = True
        SEGMENT_BYTE_CNT = self.SEGMENT_BYTE_CNT
        SEGMENT_CNT = self.SEGMENT_CNT
        USE_SOF = self.USE_SOF
        ERROR_WIDTH = self.ERROR_WIDTH

        while ag_data:
            try:
                _segmentIndex, data, user = _Axi4StreamSegmentedWord.popSegmentWordFromAgentData(ag_data, SEGMENT_CNT)
            except IndexError:
                break
            enable = bool(user.enable)
            if data_B:
                assert enable, "All segments between sof-eof must have enable=1 or whole word must have valid=0"
            else:
                if not enable:
                    # skipping unused segments before end of frame
                    continue

            if USE_SOF:
                sof = bool(user.sof)
                assert sof == first, ("Soft must be 1 in the first segment of the frame", sof, first)
            else:
                sof = first

            if ERROR_WIDTH:
                err |= int(user.err)

            eof = bool(user.eof)
            empty = int(user.empty)
            if empty != 0:
                assert eof, "non-full word in the middle of the packet"

            for i in range(SEGMENT_BYTE_CNT - empty):
                d = get_bit_range(data.val, i * 8, 8)
                if get_bit_range(data.vld_mask, i * 8, 8) != 0xff:
                    raise AssertionError(
                        "Data not valid but it should be"
                        f' based on value of "empty" B_i:{i:d}, empty:{empty:d}, vld_mask:0x{data.vld_mask:x}')
                data_B.append(d)

            if first:
                segmentIndex = _segmentIndex
                first = False

            if eof:
                break

        if not eof:
            if data_B:
                raise ValueError("Unfinished frame", data_B)
            else:
                raise ValueError("No frame available")

        return segmentIndex, data_B, err

