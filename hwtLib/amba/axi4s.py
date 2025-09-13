from typing import  Union

from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hwIOs.agents.rdVldSync import UniversalRdVldSyncAgent
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi_common import Axi_user, Axi_id, Axi_hs, Axi_strb
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.intfIpMeta import IntfIpMeta


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
    tuple[HBitsConst, HBitsConst, HBitsConst, HBitsConst],
    tuple[HBitsConst, HBitsConst, HBitsConst],
    tuple[HBitsConst, HBitsConst]
]


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
