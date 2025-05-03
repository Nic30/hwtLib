from collections import deque
from typing import List, Tuple, Union, Sequence, Generator, Optional, Deque, \
    Self

from hdlConvertorAst.to.hdlUtils import iter_with_last
from hwt.code import segment_get, Concat
from hwt.hObjList import HObjList
from hwt.hdl.const import HConst
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.structValBase import HStructConstBase
from hwt.hwIOs.agents.rdVldSync import UniversalRdVldSyncAgent
from hwt.hwIOs.hwIOStruct import HdlType_to_HwIO
from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.amba.axi4s import Axi4StreamFrameUtils
from hwtLib.amba.axi_common import Axi_user, Axi_hs
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from hwtLib.types.ctypes import uint8_t
from hwtSimApi.hdlSimulator import HdlSimulator
from pyMathBitPrecise.bit_utils import get_bit_range


class Axi4StreamSegmented(Axi_hs, Axi_user):
    """
    Xilinx/AMD Segmented Axi4Stream interface used for 100G+ Ethernet
    https://docs.amd.com/r/1.3-English/pg314-versal-mrmac/Segmented-Mode?tocId=bPOyhICzaCLnbaKgrT0K4g
    
    :ivar ~.SEGMENT_CNT: number of segments of the bus
    :ivar ~.SEGMENT_DATA_WIDTH: width of 1 segment of data signal
    :ivar ~.ERROR_WIDTH: width of 1 segment of "err" signal (can be 0)
    :ivar ~.SUPPORT_ZLP: if True "empty" signal 1b is wider and Zero Length Packets are supported
    :ivar ~.USE_SOF: if True sof is present in user struct,
        sof + enable potentially allows for sparse streams (frame continuing in not directly consequent segment)
    :irar ~.PACK_SEGMENT_BITS: if True the bits for sof, eof, enable, empty and err are packed together to a single
        bit vector, this is beneficial for smaller code size, but it makes harder to read the simulation wave
    :note: user signal is used to encode bus state, format is described in :meth:`Axi4StreamSegmented.hwDeclr`
    
    Typical configuration for Ethernet:
    
    Ethernet DATA_WIDTH SEGMENT_CNT Frequency[MHz]
    ======== ========== =========== ==============
    40G      128        1           312.5
    50G      256        2           195.3125
    100G     384        3           260.5
    400G     1024       4           400
    
    https://www.xilinx.com/content/dam/xilinx/publications/presentations/xilinx_network_security_offerings.pdf
    https://www.intel.com/content/www/us/en/docs/programmable/773413.html

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.SEGMENT_CNT:int = HwParam(4)
        self.SEGMENT_DATA_WIDTH:int = HwParam(64)
        self.BYTE_WIDTH:int = HwParam(8)
        self.SUPPORT_ZLP:bool = HwParam(False)
        self.USE_SOF:bool = HwParam(False)
        self.ERROR_WIDTH:int = HwParam(0)
        self.PACK_SEGMENT_BITS:bool = HwParam(False)

    @staticmethod
    def _hasEmpty(SEGMENT_DATA_WIDTH: int, BYTE_WIDTH: int, SUPPORT_ZLP: bool):
        return SEGMENT_DATA_WIDTH > BYTE_WIDTH or SUPPORT_ZLP

    @staticmethod
    def _getWidthOfEmpty(SEGMENT_DATA_WIDTH: int, BYTE_WIDTH: int, SUPPORT_ZLP: bool):
        return log2ceil((SEGMENT_DATA_WIDTH // BYTE_WIDTH) + (1 if SUPPORT_ZLP else 0))

    @override
    def hwDeclr(self):
        SEGMENT_CNT = self.SEGMENT_CNT
        BYTE_WIDTH = self.BYTE_WIDTH
        SEGMENT_DATA_WIDTH = self.SEGMENT_DATA_WIDTH
        assert SEGMENT_DATA_WIDTH > 0, (SEGMENT_DATA_WIDTH, BYTE_WIDTH)
        assert SEGMENT_DATA_WIDTH % BYTE_WIDTH == 0, (SEGMENT_DATA_WIDTH, BYTE_WIDTH)
        assert BYTE_WIDTH <= SEGMENT_DATA_WIDTH, (SEGMENT_DATA_WIDTH, BYTE_WIDTH)
        USE_EMPTY = self._hasEmpty(SEGMENT_DATA_WIDTH, BYTE_WIDTH, self.SUPPORT_ZLP)
        EMPTY_WIDTH = self._getWidthOfEmpty(SEGMENT_DATA_WIDTH, BYTE_WIDTH, self.SUPPORT_ZLP)

        # :note: 1st member of struct is on bit 0
        self.USER_SEGMENT_T = HStruct(
            # ENABLE 1 indicates that the associated data signal contains valid data,
            # and that the other flags on the associated user_* signals are valid
            # :note: enable is there to spare MUXes on for other struct members in not populated segments
            (BIT, "enable"),
            # SOF 1 indicates that the associated data segment contains the beginning of a new frame
            * (((BIT, "sof"),) if self.USE_SOF else ()),
            # EOF indicates end of frame
            (BIT, "eof"),
            # Err indicates error in frame
            * (((HBits(self.ERROR_WIDTH), "err"),) if self.ERROR_WIDTH else ()),
            # Empty indicates the number of empty (unused) bytes in the final (EOP) segment.
            # Valid only in the segment where EOP and ENA are asserted to 1.
            # for 8B interface: 0 == 8 bytes valid, 7 == 1 byte valid, ...
            * (((HBits(EMPTY_WIDTH), "empty"),) if USE_EMPTY else ()),
        )
        if self.PACK_SEGMENT_BITS:
            self.data = HwIOVectSignal(SEGMENT_CNT * self.SEGMENT_DATA_WIDTH)
            self.user = HwIOVectSignal(SEGMENT_CNT * self.USER_SEGMENT_T.bit_length())
        else:
            self.data = HObjList(HwIOVectSignal(self.SEGMENT_DATA_WIDTH) for _ in range(SEGMENT_CNT))
            self.user = HObjList(HdlType_to_HwIO().apply(self.USER_SEGMENT_T) for _ in range(SEGMENT_CNT))

        Axi_hs.hwDeclr(self)

    def unpackSegment(self, segmentIndex:int, v=None):
        if v is None:
            v = self
        data = segment_get(v.data, self.SEGMENT_DATA_WIDTH, segmentIndex)
        user = segment_get(v.user, self.USER_SEGMENT_T.bit_length(), segmentIndex)
        return data, user._reinterpret_cast(self.USER_SEGMENT_T)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi4StreamSegmentedAgent(sim, self)


# tuple of segments
Axi4StreamSegmentedAgentWordType = Tuple[Tuple[HBitsConst, HConst], ...]


class Axi4StreamSegmentedAgent(BaseAxiAgent, UniversalRdVldSyncAgent):
    """
    Simulation agent for :class:`.Axi4StreamSegmented` interface

    input/output data stored in list under "data" property
    data contains tuples
    """

    def __init__(self, sim: HdlSimulator, hwIO: Axi4StreamSegmented, allowNoReset=False):
        UniversalRdVldSyncAgent.__init__(self, sim, hwIO, allowNoReset=allowNoReset)
        self.DATA_SEGMENT_T = HBits(hwIO.SEGMENT_DATA_WIDTH)
        self.DATA_SEGMENT_INVALID = self.DATA_SEGMENT_T.from_py(None)
        if hwIO.PACK_SEGMENT_BITS:
            assert self._sigCnt == 2, ('expect only "data", "user" signals', self._signals)
            self.USER_SEGMENT_PACKED_T = HBits(hwIO.USER_SEGMENT_T.bit_length())
            self.USER_WORD_T = HBits(self.USER_SEGMENT_PACKED_T.bit_length() * hwIO.SEGMENT_CNT)
        else:
            assert self._sigCnt == 2 * hwIO.SEGMENT_CNT, ('expect only "data", "user" signals', self._signals)
            self.USER_SEGMENT_DISABLED = hwIO.USER_SEGMENT_T.from_py({"enable":0})
        self.USE_EMPTY = hwIO._hasEmpty(hwIO.SEGMENT_DATA_WIDTH, hwIO.BYTE_WIDTH, hwIO.SUPPORT_ZLP)

    def get_data(self):
        hwIO: Axi4StreamSegmented = self.hwIO
        USER_SEGMENT_T = hwIO.USER_SEGMENT_T
        if hwIO.PACK_SEGMENT_BITS:
            data = hwIO.data.read()
            _user = hwIO.user.read()
            DW = hwIO.SEGMENT_DATA_WIDTH
            data = [data[(s + 1) * DW: s * DW] for s in range(hwIO.SEGMENT_CNT)]
            UW = self.USER_SEGMENT_PACKED_T.bit_length()
            user = []
            USER_SEGMENT_PACKED_T = self.USER_SEGMENT_PACKED_T
            for s in range(hwIO.SEGMENT_CNT):
                userSegment = _user[(s + 1) * UW: s * UW]
                userSegment = USER_SEGMENT_PACKED_T.from_py(userSegment.val, userSegment.vld_mask)._reinterpret_cast(USER_SEGMENT_T)
                user.append(userSegment)
        else:
            USE_SOF = hwIO.USE_SOF
            ERROR_WIDTH = hwIO.ERROR_WIDTH
            USE_EMPTY = self.USE_EMPTY
            data = [d.read() for d in hwIO.data]
            user = []
            for u in hwIO.user:
                uVal = {
                    "enable": u.enable.read(),
                    "eof": u.eof.read(),
                }
                if USE_EMPTY:
                    uVal["empty"] = u.empty.read()
                if ERROR_WIDTH:
                    uVal["err"] = u.err.read()
                if USE_SOF:
                    uVal["sof"] = u.sof.read()
                user.append(USER_SEGMENT_T.from_py(uVal))
        return (tuple(data), tuple(user))

    def set_data(self, dataWord: Axi4StreamSegmentedAgentWordType):
        """
        :param dataWord: tuple of segments
        """
        hwIO: Axi4StreamSegmented = self.hwIO
        USE_SOF = hwIO.USE_SOF
        ERROR_WIDTH = hwIO.ERROR_WIDTH
        USE_EMPTY = self.USE_EMPTY
        if dataWord is None:
            if hwIO.PACK_SEGMENT_BITS:
                hwIO.data.write(None)
                hwIO.user.write(None)
            else:
                for d in hwIO.data:
                    d.write(None)
                for u in hwIO.user:
                    u.enable.write(None)
                    if USE_SOF:
                        u.sof.write(None)
                    u.eof.write(None)
                    if ERROR_WIDTH:
                        u.err.write(None)
                    if USE_EMPTY:
                        u.empty.write(None)
        else:
            data = []
            user = []
            for d, u in dataWord:
                data.append(d)
                user.append(u)

            paddingSegmentCnt = hwIO.SEGMENT_CNT - len(dataWord)
            if paddingSegmentCnt:
                # add padding
                for _ in range(paddingSegmentCnt):
                    data.append(self.DATA_SEGMENT_INVALID)
                    user.append(self.USER_SEGMENT_DISABLED)

            if hwIO.PACK_SEGMENT_BITS:
                data = Concat(*reversed(data))  # data[0] to LSB side
                hwIO.data.write(data)
                userPacked = Concat(*reversed(list(u._reinterpret_cast(self.USER_SEGMENT_PACKED_T) for u in user)))
                hwIO.user.write(userPacked)
            else:
                for dIO, d in zip(hwIO.data, data):
                    dIO.write(d)
                for uIO, u in zip(hwIO.user, user):
                    uIO.enable.write(u.enable)
                    if USE_SOF:
                        uIO.sof.write(u.sof)
                    uIO.eof.write(u.eof)
                    if ERROR_WIDTH:
                        uIO.err.write(u.err)
                    if USE_EMPTY:
                        uIO.empty.write(u.empty)


_Axi4StreamSegmentedWordOfSegment = Tuple[HBitsConst, HConst]


class _Axi4StreamSegmentedWord():
    """
    :ivar segmentWords: word of data and control signals encoded in user signal for a single segment
    """

    def __init__(self, segmentWords:Tuple[Deque[HBitsConst], Deque[HConst]], SEGMENT_CNT:int):
        self.segmentWords = segmentWords
        self.SEGMENT_CNT = SEGMENT_CNT

    def empty(self):
        return not self.segmentWords[0]

    def popleft(self):
        segmentIndex = self.SEGMENT_CNT - len(self.segmentWords[0])
        return (segmentIndex, self.segmentWords[0].popleft(), self.segmentWords[1].popleft())

    @classmethod
    def popSegmentWordFromAgentData(cls, ag_data:Deque[Tuple[HBitsConst, HConst]], SEGMENT_CNT:int) -> Self:
        cur = ag_data[0]
        if not isinstance(cur, _Axi4StreamSegmentedWord):
            segments = (deque(cur[0]), deque(cur[1]))
            cur = ag_data[0] = _Axi4StreamSegmentedWord(segments, SEGMENT_CNT)

        segmentData = cur.popleft()
        if cur.empty():
            ag_data.popleft()

        return segmentData


class Axi4StreamSegmentedFrameUtils(Axi4StreamFrameUtils):

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

    @override
    @classmethod
    def from_HwIO(cls, axiss: Axi4StreamSegmented):
        return cls(axiss.SEGMENT_DATA_WIDTH,
                   axiss.SEGMENT_CNT,
                   axiss.USER_SEGMENT_T,
                   SUPPORT_ZLP=axiss.SUPPORT_ZLP,
                   USE_SOF=axiss.USE_SOF,
                   ERROR_WIDTH=axiss.ERROR_WIDTH,
                   PACK_SEGMENT_BITS=axiss.PACK_SEGMENT_BITS)

    @override
    def pack_frame(self, structVal: Union[HConst, Sequence[int]])\
            ->Generator[Tuple[Optional[HBitsConst], HBitsConst], None, None]:
        """
        pack data of structure into words on Axi4StreamSegmented interface
        
        :param structVal: value to be send, HConst instance or list of int for each byte
        
        :returns: generator of tuples tuples (data, USER_SEGMENT_T)
        """
        if not isinstance(structVal, HConst):
            try:
                valByteCnt = len(structVal)
            except:
                structVal = tuple(structVal)
                valByteCnt = len(structVal)

            if valByteCnt != 0:
                structVal = uint8_t[valByteCnt].from_py(structVal)
            else:
                structVal = []

        byte_cnt = self.SEGMENT_BYTE_CNT
        USER_SEGMENT_T = self.USER_SEGMENT_T
        USE_SOF = self.USE_SOF
        USE_EMPTY = self.USE_EMPTY
        ERROR_WIDTH = self.ERROR_WIDTH
        if structVal == []:
            userData = {"enable":1, "eof":1}
            if USE_EMPTY:
                userData["empty"] = byte_cnt
            if USE_SOF:
                userData["sof"] = 1
            if ERROR_WIDTH:
                userData["err"] = 0

            yield (None, USER_SEGMENT_T.from_py(userData))
            return

        dataWidth = self.SEGMENT_DATA_WIDTH
        words = iterBits(structVal, bitsInOne=dataWidth,
                         skipPadding=False, fillup=True)
        first = True
        for last, data in iter_with_last(words):
            assert data._dtype.bit_length() == dataWidth, data._dtype.bit_length()
            sof = first
            if first:
                first = False
            eof = last

            userData = {"enable":1, "eof":eof}
            if USE_EMPTY:
                if last:
                    leftOverSize = (structVal._dtype.bit_length() // self.BYTE_WIDTH) % byte_cnt
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

    def concatWordBits(self, frameBeats: Sequence[Tuple[HBitsConst, HStructConstBase]]):
        for data, user in frameBeats:
            word = [data, ]  # in lowest bits first format
            for f in user._dtype.fields:
                word.append(getattr(user, f.name))

            yield Concat(*reversed(word))

    @override
    def send_bytes(self, data_B:Union[bytes, List[int]], ag_data:Deque[Axi4StreamSegmentedAgentWordType], offset:int=0) -> List[Tuple[int, int, int]]:
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
            # possibly fill unused segments into last word
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
    def receive_bytes(self, ag_data:Deque[Tuple[HBitsConst, HConst]]) -> Tuple[int, List[Union[int, HBitsConst]], bool]:
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
                ERROR_WIDTH |= int(user.err)

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

