from math import ceil
from typing import List, Tuple, Union, Deque, Generator, Optional, Sequence

from hwt.code import Concat
from hwt.hdl.const import HConst
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.utils import HConst_from_words
from hwt.hwIOs.agents.rdVldSync import UniversalRdVldSyncAgent
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwParam import HwParam
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.amba.axi_common import Axi_user, Axi_id, Axi_hs, Axi_strb
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from hwtLib.types.ctypes import uint8_t
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.intfIpMeta import IntfIpMeta
from pyMathBitPrecise.bit_utils import mask, get_bit, \
    get_bit_range, set_bit


# http://www.xilinx.com/support/documentation/ip_documentation/ug761_axi_reference_guide.pdf
class Axi4Stream(Axi_hs, Axi_id, Axi_user, Axi_strb):
    """
    AMBA AXI-stream interface
    https://static.docs.arm.com/ihi0051/a/IHI0051A_amba4_axi4_stream_v1_0_protocol_spec.pdf

    :ivar ~.IS_BIGENDIAN: HwParam which specifies if interface uses bigendian
        byte order or little-endian byte order

    :ivar ~.DATA_WIDTH: HwParam which specifies width of data signal
    :ivar ~.HAS_STRB: if set strb signal is present
    :ivar ~.HAS_KEEP: if set keep signal is present
    :ivar ~.ID_WIDTH: if > 0 id signal is present and this is it's width
    :ivar ~.DEST_WIDTH: if > 0 dest signal is present and this is it's width

    :attention: no checks are made for endianity, this is just information
    :note: bigendian for interface means that items which are send through
        this interface have reversed byte endianity.
        That means that most significant byte is is on lower address
        than les significant ones
        e.g. little endian value 0x1a2b will be 0x2b1a
        but iterface itselelf is not reversed in any way

    :ivar ~.id: optional signal wich specifies id of transaction
    :ivar ~.dest: optional signal which specifies destination of transaction
    :ivar ~.data: main data signal
    :ivar ~.keep: optional signal which signalize which bytes
                should be keept and which should be discarded
    :ivar ~.strb: optional signal which signalize which bytes are valid
    :ivar ~.last: signal which if high this data is last in this frame
    :ivar ~.user: optional signal which can be used for arbitrary purposes

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.IS_BIGENDIAN:bool = HwParam(False)
        self.USE_STRB:bool = HwParam(False)
        self.USE_KEEP:bool = HwParam(False)

        Axi_id.hwConfig(self)
        self.DEST_WIDTH:int = HwParam(0)
        self.DATA_WIDTH:int = HwParam(64)
        Axi_user.hwConfig(self)

    @override
    def hwDeclr(self):
        Axi_id.hwDeclr(self)

        if self.DEST_WIDTH:
            self.dest = HwIOVectSignal(self.DEST_WIDTH)

        self.data = HwIOVectSignal(self.DATA_WIDTH)

        if self.USE_STRB:
            Axi_strb.hwDeclr(self)

        if self.USE_KEEP:
            self.keep = HwIOVectSignal(self.DATA_WIDTH // 8)

        Axi_user.hwDeclr(self)
        self.last = HwIOSignal()

        super(Axi4Stream, self).hwDeclr()

    @override
    def _getIpCoreIntfClass(self):
        return IP_AXI4Stream

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi4StreamAgent(sim, self)


class Axi4StreamAgent(BaseAxiAgent, UniversalRdVldSyncAgent):
    """
    Simulation agent for :class:`.Axi4Stream` interface

    input/output data stored in list under "data" property
    data contains tuples

    Format of data tuples is derived from signals on Axi4Stream interface
    Order of values corresponds to definition of interface signals.
    If all signals are present format of tuple will be
    (id, dest, data, strb, keep, user, last)
    """

    def __init__(self, sim: HdlSimulator, hwIO: Axi4Stream, allowNoReset=False):
        UniversalRdVldSyncAgent.__init__(self, sim, hwIO, allowNoReset=allowNoReset)


Axi4StreamAgentWordType = Union[
    Tuple[HBitsConst, HBitsConst, HBitsConst, HBitsConst],
    Tuple[HBitsConst, HBitsConst, HBitsConst],
    Tuple[HBitsConst, HBitsConst]
]


class Axi4StreamFrameUtils():

    def __init__(self, DATA_WIDTH: int, USE_STRB=False, USE_KEEP=False, USE_ID=False, BYTE_WIDTH=8):
        self.DATA_WIDTH = DATA_WIDTH
        self.BYTE_WIDTH = BYTE_WIDTH
        self.BYTE_CNT = DATA_WIDTH // BYTE_WIDTH
        self.USE_STRB = USE_STRB
        self.USE_KEEP = USE_KEEP
        self.USE_ID = USE_ID
        self.maskT = HBits(DATA_WIDTH // self.BYTE_WIDTH)

    @classmethod
    def from_HwIO(cls, axis: Axi4Stream):
        USE_ID = bool(getattr(axis, "ID_WIDTH", 0))
        if getattr(axis, "USER_WIDTH", 0):
            raise NotImplementedError()

        USE_KEEP = hasattr(axis, "keep")
        USE_STRB = hasattr(axis, "strb")
        if USE_KEEP and USE_STRB:
            raise NotImplementedError()
        return Axi4StreamFrameUtils(axis.DATA_WIDTH, USE_STRB=USE_STRB, USE_KEEP=USE_KEEP, USE_ID=USE_ID)

    @staticmethod
    def _getWordDataFn(wordTuple:Tuple[HConst]):
        return wordTuple[0]

    def pack_frame(self, structVal: Union[HConst, Sequence[int]])\
            ->Generator[Union[Tuple[Optional[int], int, int],
                               Tuple[Optional[int], int]], None, None]:
        """
        pack data of structure into words on axis interface
        Words are tuples (data, last) or (data, mask, last) depending on args.
        
        :param structVal: value to be send, HConst instance or list of int for each byte
        
        :returns: generator of tuples (data, strb, isLast), strb is omitted if withStrb=False
        """
        DATA_WIDTH = self.DATA_WIDTH
        withStrb = self.USE_STRB or self.USE_KEEP
        if self.USE_STRB and  self.USE_KEEP:
            raise NotImplementedError()
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

        if structVal == []:
            if withStrb:
                yield (None, 0, 1)
            else:
                yield (None, 1)
            return

        if withStrb:
            byte_cnt = DATA_WIDTH // 8

        words = iterBits(structVal, bitsInOne=DATA_WIDTH,
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

    def unpack_frame(self, structT: HdlType, frameData: Deque[Union[HBitsConst, int]]) -> HConst:
        """
        opposite of :meth:`~.pack_frame"
        """
        res = HConst_from_words(structT, frameData, self._getWordDataFn, self.DATA_WIDTH)
        for _ in range(ceil(structT.bit_length() / self.DATA_WIDTH)):
            frameData.popleft()

        return res

    def concatWordBits(self, frameBeats: Sequence[Tuple[HBitsConst, int, int]]):
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

    def receive_bytes(self, ag_data: Deque[Axi4StreamAgentWordType]) -> Tuple[int, List[int]]:
        """
        :param ag_data: list of axi stream words, number of item in tuple depends on use_keep and use_id
        :param use_keep: specifies if input tuples contain keep mask
        :param use_id: specifies if input tuples contain axi stream id
        :param D_B: number of bytes in word
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
                assert offset_mask & keep &strb == 0, (offset_mask, strb, keep)
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

    def send_bytes(self, data_B: Union[bytes, List[int]], ag_data: Deque[Axi4StreamAgentWordType], offset:int=0)\
            ->List[Tuple[int, int, int]]:
        if data_B:
            if isinstance(data_B, bytes):
                data_B = [int(x) for x in data_B]
            t = uint8_t[len(data_B) + offset]
            _data_B = t.from_py([None for _ in range(offset)] + data_B)
        else:
            _data_B = data_B
        # :attention: strb signal is reinterpreted as a keep signal
        f = self.pack_frame(_data_B)
        ag_data.extend(f)
        return f


def axi4s_receive_bytes(axis: Axi4Stream) -> Tuple[int, List[int]]:
    """
    Read data from AXI Stream agent in simulation
    and use keep signal to mask out unused bytes
    """
    ag_data = axis._ag.data
    fu = Axi4StreamFrameUtils.from_HwIO(axis)
    return fu.receive_bytes(ag_data)


def axi4s_send_bytes(axis: Axi4Stream, data_B: Union[List[int], bytes], offset=0) -> None:
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
    fu = Axi4StreamFrameUtils.from_HwIO(axis)
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


class IP_AXI4Stream(IntfIpMeta):
    """
    Class which specifies how to describe Axi4Stream interfaces in IP-core
    """

    def __init__(self):
        super().__init__()
        self.name = "axis"
        self.quartus_name = "axi4stream"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {
            'id': "TID",
            'dest': "TDEST",
            'data': "TDATA",
            'strb': "TSTRB",
            'keep': "TKEEP",
            'user': 'TUSER',
            'last': "TLAST",
            'valid': "TVALID",
            'ready': "TREADY"
        }
        self.quartus_map = {
            k: v.lower() for k, v in self.map.items()
        }
