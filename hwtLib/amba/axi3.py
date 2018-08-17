from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import VectSignal, Signal
from hwt.synthesizer.param import Param
from hwtLib.amba.axi3Lite import Axi3Lite_addr, Axi3Lite, Axi3Lite_r, Axi3Lite_b,\
    IP_Axi3Lite
from hwtLib.amba.axi_intf_common import AxiMap, Axi_id
from hwtLib.amba.axis import AxiStream_withId
from hwtLib.amba.sim.agentCommon import BaseAxiAgent


#####################################################################
class Axi3_addr(Axi3Lite_addr, Axi_id):
    """
    Axi3 address channel interface
    """
    LEN_WIDTH = 4
    LOCK_WIDTH = 2

    def _config(self):
        Axi3Lite_addr._config(self)
        Axi_id._config(self)

    def _declr(self):
        Axi3Lite_addr._declr(self)
        Axi_id._declr(self)
        self.burst = VectSignal(2)
        self.cache = VectSignal(4)
        self.len = VectSignal(self.LEN_WIDTH)
        self.lock = VectSignal(self.LOCK_WIDTH)
        self.prot = VectSignal(3)
        self.size = VectSignal(3)

    def _initSimAgent(self):
        self._ag = Axi3_addrAgent(self)


class Axi3_addr_withUser(Axi3_addr):
    def _config(self):
        Axi3_addr._config(self)
        self.USER_WIDTH = Param(5)

    def _declr(self):
        Axi3_addr._declr(self)
        self.user = VectSignal(self.USER_WIDTH)

    def _initSimAgent(self):
        self._ag = Axi3_addr_withUserAgent(self)


class Axi3_addrAgent(BaseAxiAgent):
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

        return (_id, addr, burst, cache, _len, lock, prot, size)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.write

        if data is None:
            data = [None for _ in range(9)]

        _id, addr, burst, cache, _len, lock, prot, size = data

        w(_id, intf.id)
        w(addr, intf.addr)
        w(burst, intf.burst)
        w(cache, intf.cache)
        w(_len, intf.len)
        w(lock, intf.lock)
        w(prot, intf.prot)
        w(size, intf.size)


class Axi3_addr_withUserAgent(BaseAxiAgent):
    """
    Simulation agent for :class:`.Axi3_addr_withUser` interface

    input/output data stored in list under "data" property
    data contains tuples (id, addr, burst, cache, len, lock, prot, size, qos, user)
    """

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
        user = r(intf.user)
        return (_id, addr, burst, cache, _len, lock, prot, size, user)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.write

        if data is None:
            data = (None for _ in range(9))

        _id, addr, burst, cache, _len, lock, prot, size, user = data

        w(_id, intf.id)
        w(addr, intf.addr)
        w(burst, intf.burst)
        w(cache, intf.cache)
        w(_len, intf.len)
        w(lock, intf.lock)
        w(prot, intf.prot)
        w(size, intf.size)
        w(user, intf.user)


#####################################################################
class Axi3_w(AxiStream_withId):
    """
    Axi3 write channel interface
    """
    pass


#####################################################################
class Axi3_r(Axi3Lite_r, Axi_id):
    """
    Axi 3 read channel interface
    """
    def _config(self):
        Axi_id._config(self)
        Axi3Lite_r._config(self)

    def _declr(self):
        Axi_id._declr(self)
        Axi3Lite_r._declr(self)
        self.last = Signal()

    def _initSimAgent(self):
        self._ag = Axi3_rAgent(self)


class Axi3_rAgent(BaseAxiAgent):
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
class Axi3_b(Axi3Lite_b, Axi_id):
    """
    Axi3 write response channel interface
    """
    def _config(self):
        Axi_id._config(self)
        Axi3Lite_b._config(self)

    def _declr(self):
        Axi_id._declr(self)
        Axi3Lite_b._declr(self)

    def _initSimAgent(self):
        self._ag = Axi3_bAgent(self)


class Axi3_bAgent(BaseAxiAgent):
    """
    Simulation agent for :class:`.Axi3_b` interface

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
class Axi3(Axi3Lite):
    """
    Axi3 bus interface
    """
    LOCK_WIDTH = 2
    LEN_WIDTH = 4

    def _config(self):
        Axi3Lite._config(self)
        self.ID_WIDTH = Param(6)

    def _declr(self):
        with self._paramsShared():
            self.aw = Axi3_addr()
            self.ar = Axi3_addr()
            self.w = Axi3_w()
            self.r = Axi3_r(masterDir=DIRECTION.IN)
            self.b = Axi3_b(masterDir=DIRECTION.IN)

    def _getIpCoreIntfClass(self):
        return IP_Axi3


class Axi3_withAddrUser(Axi3):
    """
    Axi3 bus interface with user signals on address channels
    """
    def _config(self):
        Axi3._config(self)
        self.USER_WIDTH = Param(3)

    def _declr(self):
        with self._paramsShared():
            self.aw = Axi3_addr_withUser()
            self.ar = Axi3_addr_withUser()
            self.w = Axi3_w()
            self.r = Axi3_r(masterDir=DIRECTION.IN)
            self.b = Axi3_b(masterDir=DIRECTION.IN)

    def _getIpCoreIntfClass(self):
        return IP_Axi3_withAddrUser


class IP_Axi3(IP_Axi3Lite):
    """
    IP core interface meta for Axi3 interface
    """
    def __init__(self,):
        super(IP_Axi3, self).__init__()
        self.quartus_name = "axi"
        self.xilinx_protocol_name = "AXI3"
        A_SIGS = ['id', 'burst', 'cache', 'len', 'lock', 'prot', 'size', 'qos']
        AxiMap('ar', A_SIGS, self.map['ar'])
        AxiMap('r', ['id', 'last'], self.map['r'])
        AxiMap('aw', A_SIGS, self.map['aw'])
        AxiMap('w', ['id', 'last'], self.map['w'])
        AxiMap('b', ['id'], self.map['b'])

    def postProcess(self, component, entity, allInterfaces, thisIf):
        self.endianness = "little"

        def param(name, val):
            return self.addSimpleParam(thisIf, name, str(val))
        # [TODO] width as expression instead of int
        param("ADDR_WIDTH", thisIf.aw.addr._dtype.bit_length())
        param("MAX_BURST_LENGTH", 256)
        param("NUM_READ_OUTSTANDING", 5)
        param("NUM_WRITE_OUTSTANDING", 5)
        param("PROTOCOL", self.xilinx_protocol_name)
        param("READ_WRITE_MODE", "READ_WRITE")
        param("SUPPORTS_NARROW_BURST", 0)


class IP_Axi3_withAddrUser(IP_Axi3):
    """
    IP core interface meta for Axi3_withAddrUser interface
    """
    def __init__(self):
        super(IP_Axi3_withAddrUser, self).__init__()
        AxiMap('ar', ['user'], self.map['ar'])
        AxiMap('aw', ['user'], self.map['aw'])

    def postProcess(self, component, entity, allInterfaces, thisIf):
        super().postProcess(component, entity, allInterfaces, thisIf)
        self.addWidthParam(thisIf, "AWUSER_WIDTH", thisIf.USER_WIDTH)
        self.addWidthParam(thisIf, "ARUSER_WIDTH", thisIf.USER_WIDTH)
