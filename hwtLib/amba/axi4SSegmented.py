from collections import deque
from math import ceil
from typing import Union, Deque, \
    Self

from hwt.code import segment_get, Concat
from hwt.hObjList import HObjList
from hwt.hdl.const import HConst
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.hwIOs.agents.rdVldSync import UniversalRdVldSyncAgent
from hwt.hwIOs.hwIOStruct import HdlType_to_HwIO
from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi_common import Axi_user, Axi_hs
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from hwtSimApi.hdlSimulator import HdlSimulator


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
    40G       128       1           312.5 [0]
    50G       256       2           195.3125 [0]
    100G      384       3           260.5 [0]
    100G      512       1           390.625 [2]
    400G     1024       8           390.625 [3]
    600G     1536       12          390.625 [3]
    
    [0] https://www.xilinx.com/content/dam/xilinx/publications/presentations/xilinx_network_security_offerings.pdf
    [1] https://www.intel.com/content/www/us/en/docs/programmable/773413.html
    [2] https://cdrdv2.intel.com/v1/dl/getContent/827074?fileName=ug20085-683100-827074.pdf
    [3] https://docs.amd.com/r/en-US/pg369-dcmac
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
    def getWastedBandwidthPercent(SEGMENT_CNT:int, DATA_WIDTH: int, PACKET_WIDTH: int):
        assert DATA_WIDTH % SEGMENT_CNT == 0, (DATA_WIDTH, SEGMENT_CNT)
        SEGMENT_WIDTH = DATA_WIDTH // SEGMENT_CNT
        leftover = PACKET_WIDTH % SEGMENT_WIDTH
        wasted = SEGMENT_WIDTH - leftover
        packetSegmentCnt = ceil(PACKET_WIDTH / SEGMENT_WIDTH)
        return wasted / (packetSegmentCnt * SEGMENT_WIDTH)

    @classmethod
    def getEffectiveThroughput(cls, CLK_FREQ: Union[float, int], SEGMENT_CNT: int, DATA_WIDTH: int, PACKET_WIDTH: int):
        efficiency = cls.getWastedBandwidthPercent(SEGMENT_CNT, DATA_WIDTH, PACKET_WIDTH)
        return CLK_FREQ * DATA_WIDTH * (1. - efficiency)

    @classmethod
    def getMinNumberOfSegments(cls, BITRATE: Union[float, int], DATA_WIDTH: int, CLK_FREQ: float, MIN_PACKET_WIDTH: int):
        """
        :param MIN_PACKET_WIDTH: the width of most waistful packet, e.g. (64 + 1) * 8b for ethernet    
        """
        assert BITRATE <= CLK_FREQ * DATA_WIDTH
        segmentCnt = 1
        while True:
            ebpsMinPkt = cls.getEffectiveThroughput(CLK_FREQ, segmentCnt, DATA_WIDTH, MIN_PACKET_WIDTH)
            segmentWidth = DATA_WIDTH // segmentCnt
            if MIN_PACKET_WIDTH < segmentWidth:
                ebpsMinPkt = min(ebpsMinPkt, cls.getEffectiveThroughput(CLK_FREQ, segmentCnt, DATA_WIDTH, segmentWidth + 8))
            if ebpsMinPkt >= BITRATE:
                break

            segmentCnt += 1
            while DATA_WIDTH % segmentCnt != 0 or (DATA_WIDTH // segmentCnt) % 8 != 0:
                segmentCnt += 1
                if segmentCnt >= DATA_WIDTH // 8:
                    raise AssertionError("Clock frequency too low")

        return segmentCnt

    @staticmethod
    def _hasEmpty(SEGMENT_DATA_WIDTH: int, BYTE_WIDTH: int, SUPPORT_ZLP: bool):
        return SEGMENT_DATA_WIDTH > BYTE_WIDTH or SUPPORT_ZLP

    @staticmethod
    def _hasEnable(SEGMENT_CNT: int):
        return SEGMENT_CNT > 1

    @staticmethod
    def _getWidthOfEmpty(SEGMENT_DATA_WIDTH: int, BYTE_WIDTH: int, SUPPORT_ZLP: bool):
        return log2ceil((SEGMENT_DATA_WIDTH // BYTE_WIDTH) + (1 if SUPPORT_ZLP else 0))

    def resolveTypes(self):
        if hasattr(self, "USER_SEGMENT_T"):
            return

        SEGMENT_CNT = self.SEGMENT_CNT
        BYTE_WIDTH = self.BYTE_WIDTH
        SEGMENT_DATA_WIDTH = self.SEGMENT_DATA_WIDTH
        assert SEGMENT_DATA_WIDTH > 0, (SEGMENT_DATA_WIDTH, BYTE_WIDTH)
        assert SEGMENT_DATA_WIDTH % BYTE_WIDTH == 0, (SEGMENT_DATA_WIDTH, BYTE_WIDTH)
        assert BYTE_WIDTH <= SEGMENT_DATA_WIDTH, (SEGMENT_DATA_WIDTH, BYTE_WIDTH)
        USE_EMPTY = self._hasEmpty(SEGMENT_DATA_WIDTH, BYTE_WIDTH, self.SUPPORT_ZLP)
        USE_ENABLE = self._hasEnable(SEGMENT_CNT)
        EMPTY_WIDTH = self._getWidthOfEmpty(SEGMENT_DATA_WIDTH, BYTE_WIDTH, self.SUPPORT_ZLP)

        # :note: 1st member of struct is on bit 0
        self.USER_SEGMENT_T = HStruct(
            # ENABLE 1 indicates that the associated data signal contains valid data,
            # and that the other flags on the associated user_* signals are valid
            # :note: enable is there to spare MUXes on for other struct members in not populated segments
           * (((BIT, "enable"),) if USE_ENABLE else ()),
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
        self.WORD_T = HStruct(
            (HBits(SEGMENT_DATA_WIDTH)[SEGMENT_CNT], "data"),
            (self.USER_SEGMENT_T[SEGMENT_CNT], "user")
        )

    @override
    def hwDeclr(self):
        self.resolveTypes()
        SEGMENT_CNT = self.SEGMENT_CNT
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
Axi4StreamSegmentedAgentWordType = tuple[tuple[HBitsConst, HConst], ...]


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
        self.USE_ENABLE = hwIO._hasEnable(hwIO.SEGMENT_CNT)
        if hwIO.PACK_SEGMENT_BITS:
            assert self._sigCnt == 2, ('expect only "data", "user" signals', self._signals)
            self.USER_SEGMENT_PACKED_T = HBits(hwIO.USER_SEGMENT_T.bit_length())
            self.USER_WORD_T = HBits(self.USER_SEGMENT_PACKED_T.bit_length() * hwIO.SEGMENT_CNT)
        else:
            assert self._sigCnt == 2 * hwIO.SEGMENT_CNT, ('expect only "data", "user" signals', self._signals)
            self.USER_SEGMENT_DISABLED = hwIO.USER_SEGMENT_T.from_py({"enable": 0} if self.USE_ENABLE else {})
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
            USE_ENABLE = self.USE_ENABLE
            data = [d.read() for d in hwIO.data]
            user = []
            for u in hwIO.user:
                uVal = {
                    "eof": u.eof.read(),
                }
                if USE_ENABLE:
                    uVal["enable"] = u.enable.read()
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
        USE_ENABLE = self.USE_ENABLE
        USE_EMPTY = self.USE_EMPTY
        if dataWord is None:
            if hwIO.PACK_SEGMENT_BITS:
                hwIO.data.write(None)
                hwIO.user.write(None)
            else:
                for d in hwIO.data:
                    d.write(None)
                for u in hwIO.user:
                    if USE_ENABLE:
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
                    if USE_ENABLE:
                        uIO.enable.write(u.enable)
                    if USE_SOF:
                        uIO.sof.write(u.sof)
                    uIO.eof.write(u.eof)
                    if ERROR_WIDTH:
                        uIO.err.write(u.err)
                    if USE_EMPTY:
                        uIO.empty.write(u.empty)


_Axi4StreamSegmentedWordOfSegment = tuple[HBitsConst, HConst]


class _Axi4StreamSegmentedWord():
    """
    :ivar segmentWords: word of data and control signals encoded in user signal for a single segment
    """

    def __init__(self, segmentWords:tuple[Deque[HBitsConst], Deque[HConst]], SEGMENT_CNT:int):
        self.segmentWords = segmentWords
        self.SEGMENT_CNT = SEGMENT_CNT

    def empty(self):
        return not self.segmentWords[0]

    def popleft(self):
        segmentIndex = self.SEGMENT_CNT - len(self.segmentWords[0])
        return (segmentIndex, self.segmentWords[0].popleft(), self.segmentWords[1].popleft())

    @classmethod
    def popSegmentWordFromAgentData(cls, ag_data:Deque[tuple[HBitsConst, HConst]], SEGMENT_CNT:int) -> Self:
        cur = ag_data[0]
        if not isinstance(cur, _Axi4StreamSegmentedWord):
            segments = (deque(cur[0]), deque(cur[1]))
            cur = ag_data[0] = _Axi4StreamSegmentedWord(segments, SEGMENT_CNT)

        segmentData = cur.popleft()
        if cur.empty():
            ag_data.popleft()

        return segmentData


if __name__ == "__main__":

    ref = [
        # (40e9 , 128, 1, 312.5e6),
        # (50e9 , 256, 2, 195.3125e6),
        # (100e9, 384, 3, 260.5e6),
        # (100e9, 512, 1, 390.625e6),
        # (400e9, 1024, 8, 390.625e6),
        # (600e9, 1536, 12, 390.625e6),
        # (600e9, 768, 4, 1000e6),
        (100e9, 112, 4, 1000e6),

    ]

    PACKET_WIDTH = (64 + 1) * 8
    for bitrate, dataWidth, refSegmentCnt, freq in ref:
        segmentCnt = Axi4StreamSegmented.getMinNumberOfSegments(bitrate, dataWidth, freq, PACKET_WIDTH)
        print(bitrate / 1e9, segmentCnt, segmentCnt == refSegmentCnt)

