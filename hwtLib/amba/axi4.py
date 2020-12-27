from hwt.interfaces.std import VectSignal, Signal
from hwt.synthesizer.param import Param
from hwtLib.amba.axi3 import Axi3_addr, Axi3_r, Axi3_b, IP_Axi3, Axi3, _DEFAULT
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axi_intf_common import Axi_strb, Axi_hs
from hwtLib.amba.axis import AxiStream, AxiStreamAgent
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from hwtSimApi.hdlSimulator import HdlSimulator
from hwtLib.amba.constants import BURST_INCR, LOCK_DEFAULT, PROT_DEFAULT,\
    BYTES_IN_TRANS, QOS_DEFAULT, CACHE_DEFAULT


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

    def _declr(self):
        Axi3_addr._declr(self)
        self.qos = VectSignal(4)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi4_addrAgent(sim, self)


class Axi4_addrAgent(AxiStreamAgent):
    def __init__(self, sim: HdlSimulator, intf: Axi3_addr, allowNoReset=False):
        BaseAxiAgent.__init__(self, sim, intf, allowNoReset=allowNoReset)

        signals = [
            intf.id,
            intf.addr,
            intf.burst,
            intf.cache,
            intf.len,
            intf.lock,
            intf.prot,
            intf.size,
            intf.qos
        ]
        if hasattr(intf, "user"):
            signals.append(intf.user)
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
                        user=None):
        """
        Create a default AXI address transaction
        :note: transaction is created and returned but it is not added to a agent data
        """
        if size is _DEFAULT:
            D_B = self.intf._parent.DATA_WIDTH // 8
            size = BYTES_IN_TRANS(D_B)
        if self.intf.USER_WIDTH:
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
    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.data = VectSignal(self.DATA_WIDTH)
        Axi_strb._declr(self)
        self.last = Signal()
        Axi_hs._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        AxiStream._initSimAgent(self, sim)


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

    def _config(self):
        Axi4Lite._config(self)
        self.ID_WIDTH = Param(6)
        self.LOCK_WIDTH = 1
        self.ADDR_USER_WIDTH = Param(0)

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
