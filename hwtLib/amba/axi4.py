from hwt.hdlObjects.constants import DIRECTION
from hwt.interfaces.std import VectSignal, Signal
from hwt.synthesizer.param import Param
from hwtLib.amba.axiLite import AxiLite, AxiLite_b, AxiLite_r, \
    AxiLite_addr, IP_AXILite
from hwtLib.amba.axi_intf_common import AxiMap, Axi_id
from hwtLib.amba.axis import AxiStream_withId
from hwtLib.amba.sim.agentCommon import BaseAxiAgent


#####################################################################
class Axi4_addr(AxiLite_addr, Axi_id):
    def _config(self):
        AxiLite_addr._config(self)
        Axi_id._config(self)
        self.LEN_WIDTH = 8
        self.LOCK_WIDTH = Param(1)

    def _declr(self):
        AxiLite_addr._declr(self)
        Axi_id._declr(self)
        self.burst = VectSignal(2)
        self.cache = VectSignal(4)
        self.len = VectSignal(self.LEN_WIDTH)
        self.lock = VectSignal(int(self.LOCK_WIDTH))
        self.prot = VectSignal(3)
        self.size = VectSignal(3)
        self.qos = VectSignal(4)

    def _getSimAgent(self):
        return Axi4_addrAgent


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
class Axi4_r(AxiLite_r, Axi_id):
    def _config(self):
        Axi_id._config(self)
        AxiLite_r._config(self)

    def _declr(self):
        Axi_id._declr(self)
        AxiLite_r._declr(self)
        self.last = Signal()

    def _getSimAgent(self):
        return Axi4_rAgent


class Axi4_rAgent(BaseAxiAgent):
    """
    Simulation agent for :class:`.Axi4_r` interface
    
    input/output data stored in list under "data" property
    data contains tuples (id, data, resp, last)
    """
    def doRead(self, s):
        intf = self.intf
        r = s.read

        _id = r(intf.id)
        data = r(intf.data)
        resp = r(intf.resp)
        last = r(intf.last)

        return (_id, data, resp, last)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.write

        if data is None:
            data = [None for _ in range(4)]

        _id, data, resp, last = data

        w(_id, intf.id)
        w(data, intf.data)
        w(resp, intf.resp)
        w(last, intf.last)


#####################################################################
class Axi4_w(AxiStream_withId):
    pass

#####################################################################
class Axi4_b(AxiLite_b, Axi_id):
    def _config(self):
        Axi_id._config(self)
        AxiLite_b._config(self)

    def _declr(self):
        Axi_id._declr(self)
        AxiLite_b._declr(self)

    def _getSimAgent(self):
        return Axi4_bAgent


class Axi4_bAgent(BaseAxiAgent):
    """
    Simulation agent for :class:`.Axi4_b` interface
    
    input/output data stored in list under "data" property
    data contains tuples (id, resp)
    """
    def doRead(self, s):
        r = s.read
        intf = self.intf

        return r(intf.id), r(intf.resp)

    def doWrite(self, s, data):
        w = s.write
        intf = self.intf

        if data is None:
            data = [None for _ in range(2)]

        _id, resp = data

        w(_id, intf.id)
        w(resp, intf.resp)


#####################################################################
class Axi4(AxiLite):
    """
    Basic AMBA AXI4 interface
    
    :ivar ar: read address channel
    :ivar r:  read data channel
    :ivar aw: write address channel
    :ivar w: write data channel
    :ivar b: write acknowledge channel
    """
    def _config(self):
        AxiLite._config(self)
        self.ID_WIDTH = Param(6)
        self.LOCK_WIDTH = Param(1)

    def _declr(self):
        with self._paramsShared():
            self.ar = Axi4_addr()
            self.r = Axi4_r(masterDir=DIRECTION.IN)
            self.aw = Axi4_addr()
            self.w = Axi4_w()
            self.b = Axi4_b(masterDir=DIRECTION.IN)

    def _getIpCoreIntfClass(self):
        return IP_Axi4


class IP_Axi4(IP_AXILite):
    def __init__(self,):
        super().__init__()
        A_SIGS = ['id', 'burst', 'cache', 'len', 'lock', 'prot', 'size', 'qos']
        AxiMap('ar', A_SIGS, self.map['ar'])
        AxiMap('r', ['id', 'last'], self.map['r'])
        AxiMap('aw', A_SIGS, self.map['aw'])
        AxiMap('w', ['id', 'last'], self.map['w'])
        AxiMap('b', ['id'], self.map['b'])

    def postProcess(self, component, entity, allInterfaces, thisIf):
        self.endianness = "little"
        param = lambda name, val: self.addSimpleParam(thisIf, name, str(val))
        param("ADDR_WIDTH", thisIf.aw.addr._dtype.bit_length())  # [TODO] width expression
        param("MAX_BURST_LENGTH", 256)
        param("NUM_READ_OUTSTANDING", 5)
        param("NUM_WRITE_OUTSTANDING", 5)
        param("PROTOCOL", "AXI4")
        param("READ_WRITE_MODE", "READ_WRITE")
        param("SUPPORTS_NARROW_BURST", 0)
