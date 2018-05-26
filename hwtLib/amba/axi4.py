from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import VectSignal
from hwt.synthesizer.param import Param
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from hwtLib.amba.axi3 import Axi3_addr, Axi3_r, Axi3_b, IP_Axi3, Axi3


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

    def _initSimAgent(self):
        self._ag = Axi4_addrAgent(self)


class Axi4_addrAgent(BaseAxiAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.read

        addr = r(intf.addr)
        _id = r(intf.id)
        burst = r(intf.burst)
        cache = r(intf.cache)
        _len = r(intf.len)
        lock = r(intf.lock)
        prot = r(intf.prot)
        size = r(intf.size)
        qos = r(intf.qos)

        return (_id, addr, burst, cache, _len, lock, prot, size, qos)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.write

        if data is None:
            data = [None for _ in range(9)]

        _id, addr, burst, cache, _len, lock, prot, size, qos = data

        w(_id, intf.id)
        w(addr, intf.addr)
        w(burst, intf.burst)
        w(cache, intf.cache)
        w(_len, intf.len)
        w(lock, intf.lock)
        w(prot, intf.prot)
        w(size, intf.size)
        w(qos, intf.qos)


#####################################################################
class Axi4_r(Axi3_r):
    """
    Axi4 read channel interface
    (same as axi3)
    """
    pass


#####################################################################
class Axi4_w(AxiStream):
    """
    Axi4 write channel interface
    (Axi3_w without id signal)
    """
    pass


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

    def _declr(self):
        with self._paramsShared():
            self.ar = Axi4_addr()
            self.r = Axi4_r(masterDir=DIRECTION.IN)
            self.aw = Axi4_addr()
            self.w = Axi4_w()
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
