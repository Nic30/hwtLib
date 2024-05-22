from math import ceil
from typing import List, Tuple, Union, Deque

from hwt.hdl.types.bitsConst import HBitsConst
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

    Format of data tules is derived from signals on Axi4Stream interface
    Order of values coresponds to definition of interface signals.
    If all signals are present fotmat of tuple will be
    (id, dest, data, strb, keep, user, last)
    """

    def __init__(self, sim: HdlSimulator, hwIO: Axi4Stream, allowNoReset=False):
        UniversalRdVldSyncAgent.__init__(self, sim, hwIO, allowNoReset=allowNoReset)


def packAxi4SFrame(dataWidth, structVal, withStrb=False):
    """
    pack data of structure into words on axis interface
    Words are tuples (data, last) or (data, mask, last) depending on args.
    """
    if withStrb:
        byte_cnt = dataWidth // 8

    if structVal == []:
        if withStrb:
            yield (None, 0, 1)
        else:
            yield (None, 1)
        return

    words = iterBits(structVal, bitsInOne=dataWidth,
                     skipPadding=False, fillup=True)
    for last, d in iter_with_last(words):
        assert d._dtype.bit_length() == dataWidth, d._dtype.bit_length()
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


def unpackAxi4SFrame(structT: HdlType, frameData: Deque[Union[HBitsConst, int]], getDataFn=None, dataWidth=None):
    """
    opposite of packAxi4SFrame
    """
    if getDataFn is None:

        def _getDataFn(x):
            return x[0]

        getDataFn = _getDataFn

    res = HConst_from_words(structT, frameData, getDataFn, dataWidth)
    if dataWidth is None:
        dataWidth = frameData[0][0]._dtype.bit_length()

    for _ in range(ceil(structT.bit_length() / dataWidth)):
        frameData.popleft()

    return res


def _axi4s_recieve_bytes(ag_data: Deque[Union[
                                        Tuple[HBitsConst, HBitsConst, HBitsConst, HBitsConst],
                                        Tuple[HBitsConst, HBitsConst, HBitsConst],
                                        Tuple[HBitsConst, HBitsConst]]],
                        D_B: int, use_keep: bool, use_id: bool) -> Tuple[int, List[int]]:
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
    current_id = 0
    mask_all = mask(D_B)
    while ag_data:
        _d = ag_data.popleft()
        if use_id:
            if use_keep:
                id_, data, keep, last = _d
                keep = int(keep)
            else:
                id_, data, last = _d
                keep = mask_all
            id_ = int(id_)
        else:
            if use_keep:
                data, keep, last = _d
                keep = int(keep)
            else:
                data, last = _d
                keep = mask_all
            id_ = 0

        last = int(last)
        if keep == 0:
            assert not data_B, "Empty word in the middle of the packet"
            assert last, "Empty word at the beginning of the packet"
            offset = 0

        if offset is None:
            # first iteration
            # expecting potential 0s in keep and the rest 1
            for i in range(D_B):
                # i represents number of 0 from te beginning of of the keep
                # value
                if keep & (1 << i):
                    offset = i
                    break
            assert offset is not None, keep
        for i in range(D_B):
            if get_bit(keep, i):
                d = get_bit_range(data.val, i * 8, 8)
                if get_bit_range(data.vld_mask, i * 8, 8) != 0xff:
                    raise AssertionError(
                        "Data not valid but it should be"
                        f" based on strb/keep B_i:{i:d}, 0x{keep:x}, 0x{data.vld_mask:x}")
                data_B.append(d)

        if first:
            offset_mask = mask(offset)
            assert offset_mask & keep == 0, (offset_mask, keep)
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


def axi4s_recieve_bytes(axis: Axi4Stream) -> Tuple[int, List[int]]:
    """
    Read data from AXI Stream agent in simulation
    and use keep signal to mask out unused bytes
    """
    ag_data = axis._ag.data
    D_B = axis.DATA_WIDTH // 8
    USE_ID = bool(getattr(axis, "ID_WIDTH", 0))
    if getattr(axis, "USER_WIDTH", 0):
        raise NotImplementedError()

    USE_KEEP = hasattr(axis, "keep")
    USE_STRB = hasattr(axis, "strb")
    if USE_KEEP and USE_STRB:
        raise NotImplementedError()
    use_keep = USE_KEEP | USE_STRB
    return _axi4s_recieve_bytes(ag_data, D_B, use_keep, USE_ID)


def _axi4s_send_bytes(axis: Axi4Stream, data_B: List[int], withStrb:bool, offset:int)\
        ->List[Tuple[int, int, int]]:
    if data_B:
        t = uint8_t[len(data_B) + offset]
        _data_B = t.from_py([None for _ in range(offset)] + data_B)
    else:
        _data_B = data_B
    # :attention: strb signal is reinterpreted as a keep signal
    return packAxi4SFrame(axis.DATA_WIDTH, _data_B,
        withStrb=withStrb)


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
    withStrb = axis.USE_KEEP | axis.USE_STRB
    if isinstance(data_B, bytes):
        data_B = [int(x) for x in data_B]
    f = _axi4s_send_bytes(axis, data_B, withStrb, offset)
    axis._ag.data.extend(f)


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
