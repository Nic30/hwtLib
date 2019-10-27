from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import VectSignal, Signal
from hwt.synthesizer.param import Param
from hwtLib.amba.axi3 import Axi3_addr, Axi3_r, Axi3_b, IP_Axi3, Axi3
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axi_intf_common import Axi_strb, Axi_hs
from hwtLib.amba.axis import AxiStream, AxiStreamAgent
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from pycocotb.hdlSimulator import HdlSimulator


#####################################################################
class Axi4_addr(Axi3_addr):
    """
    Axi4 address channel interface
    (axi3 address channel with different size of len and lock signals
    and additional qos signal)
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


#####################################################################
class Axi4_r(Axi3_r):
    """
    Axi4 read channel interface
    (same as axi3)
    """
    pass


#####################################################################
class Axi4_w(Axi_hs, Axi_strb):
    """
    Axi4 write channel interface
    (Axi3_w without id signal)
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
    (same as axi3)
    """
    pass


#####################################################################
class Axi4(Axi3):
    """
    Basic AMBA AXI4 bus interface

    :ivar ar: read address channel
    :ivar r:  read data channel
    :ivar aw: write address channel
    :ivar w: write data channel
    :ivar b: write acknowledge channel
    """
    LEN_WIDTH = 8
    LOCK_WIDTH = 1

    def _config(self):
        Axi4Lite._config(self)
        self.ID_WIDTH = Param(6)
        self.LOCK_WIDTH = 1
        self.ADDR_USER_WIDTH = Param(0)

    def _declr(self):
        with self._paramsShared():
            self.ar = Axi4_addr()
            self.r = Axi4_r(masterDir=DIRECTION.IN)
            self.aw = Axi4_addr()
            self.w = Axi4_w()

        with self._paramsShared():
            self.b = Axi4_b(masterDir=DIRECTION.IN)

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
