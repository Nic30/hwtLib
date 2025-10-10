from typing import Optional

from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi3 import Axi3_addr, Axi3_r, Axi3_b, IP_Axi3, Axi3, _DEFAULT
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axi4s import Axi4Stream, Axi4StreamAgent
from hwtLib.amba.axi_common import Axi_strb, Axi_hs
from hwtLib.amba.constants import BURST_INCR, LOCK_DEFAULT, PROT_DEFAULT, \
    BYTES_IN_TRANS, QOS_DEFAULT, CACHE_DEFAULT
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from hwtSimApi.hdlSimulator import HdlSimulator


#####################################################################
class Axi4_addr(Axi3_addr):
    """
    Axi4 address channel interface
    (axi3 address channel with different size of len and lock signals
    and additional qos signal)

    .. hwt-autodoc::
    """
    LEN_WIDTH = 8
    LOCK_WIDTH = 1

    @override
    def hwDeclr(self):
        Axi3_addr.hwDeclr(self)
        self.qos = HwIOVectSignal(4)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi4_addrAgent(sim, self)


class Axi4_addrAgent(Axi4StreamAgent):

    def __init__(self, sim: HdlSimulator, hwIO: Axi3_addr, allowNoReset=False):
        BaseAxiAgent.__init__(self, sim, hwIO, allowNoReset=allowNoReset)

        signals = [
            hwIO.id,
            hwIO.addr,
            hwIO.burst,
            hwIO.cache,
            hwIO.len,
            hwIO.lock,
            hwIO.prot,
            hwIO.size,
            hwIO.qos
        ]
        if hasattr(hwIO, "user"):
            signals.append(hwIO.user)
        self._signals = tuple(signals)
        self._sigCnt = len(signals)

    def create_addr_req(self, addr, _len,
                        _id=0,
                        burst=BURST_INCR,
                        cache=CACHE_DEFAULT,
                        lock=LOCK_DEFAULT,
                        prot=PROT_DEFAULT,
                        size=_DEFAULT,
                        qos=QOS_DEFAULT,
                        user=None,
                        DATA_WIDTH:Optional[int]=None):
        """
        Create a default AXI address transaction
        :note: transaction is created and returned but it is not added to a agent data
        """
        if size is _DEFAULT:
            if DATA_WIDTH is None:
                axi: Axi4 = self.hwIO._parent
                D_B = axi.DATA_WIDTH // 8
            else:
                D_B = DATA_WIDTH // 8
            size = BYTES_IN_TRANS(D_B)
        if self.hwIO.USER_WIDTH:
            return (_id, addr, burst, cache, _len, lock, prot, size, qos, user)
        else:
            assert user is None
            return (_id, addr, burst, cache, _len, lock, prot, size, qos)


#####################################################################
class Axi4_r(Axi3_r):
    """
    Axi4 read channel interface
    (same as r  :class:`~.Axi3_r`)

    .. hwt-autodoc::
    """
    pass


#####################################################################
class Axi4_w(Axi_hs, Axi_strb):
    """
    Axi4 write channel interface
    (:class:`~.Axi3_w` without id signal)

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(64)

    @override
    def hwDeclr(self):
        self.data = HwIOVectSignal(self.DATA_WIDTH)
        Axi_strb.hwDeclr(self)
        self.last = HwIOSignal()
        Axi_hs.hwDeclr(self)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        Axi4Stream._initSimAgent(self, sim)


#####################################################################
class Axi4_b(Axi3_b):
    """
    Axi4 write response channel interface
    (same as :class:`~.Axi3_b`)

    .. hwt-autodoc::
    """
    pass


#####################################################################
class Axi4(Axi3):
    """
    AMBA AXI4 bus interface
    https://static.docs.arm.com/ihi0022/d/IHI0022D_amba_axi_protocol_spec.pdf

    :ivar ~.ar: read address channel
    :ivar ~.r:  read data channel
    :ivar ~.aw: write address channel
    :ivar ~.w: write data channel
    :ivar ~.b: write acknowledge channel

    .. hwt-autodoc::
    """

    LEN_WIDTH = 8
    LOCK_WIDTH = 1
    AW_CLS = Axi4_addr
    AR_CLS = Axi4_addr
    W_CLS = Axi4_w
    R_CLS = Axi4_r
    B_CLS = Axi4_b

    @override
    def hwConfig(self):
        Axi4Lite.hwConfig(self)
        self.ID_WIDTH = HwParam(6)
        self.LOCK_WIDTH = 1
        self.ADDR_USER_WIDTH = HwParam(0)

    @override
    def _getIpCoreIntfClass(self):
        return IP_Axi4


class IP_Axi4(IP_Axi3):
    """
    IP core interface meta for Axi4 interface
    """

    def __init__(self):
        super(IP_Axi4, self).__init__()
        self.quartus_name = "axi4"
        self.xilinx_protocol_name = "AXI4"
