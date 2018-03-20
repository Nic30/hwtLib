from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import VectSignal
from hwt.pyUtils.arrayQuery import single
from hwt.synthesizer.param import Param
from hwtLib.amba.axi4 import IP_Axi4, Axi4_r, Axi4_b, Axi4, Axi4_addr
from hwtLib.amba.axiLite import AxiLite_addr, AxiLite
from hwtLib.amba.axi_intf_common import AxiMap, Axi_id
from hwtLib.amba.axis import AxiStream_withId
from hwtLib.amba.sim.agentCommon import BaseAxiAgent


class Axi3_addr(Axi4_addr):
    def _config(self):
        AxiLite_addr._config(self)
        Axi_id._config(self)
        self.LEN_WIDTH = 4
        self.LOCK_WIDTH = Param(2)

    def _declr(self):
        AxiLite_addr._declr(self)
        Axi_id._declr(self)
        self.burst = VectSignal(2)
        self.cache = VectSignal(4)
        self.len = VectSignal(self.LEN_WIDTH)
        self.lock = VectSignal(int(self.LOCK_WIDTH))
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


class Axi3_w(AxiStream_withId):
    pass


class Axi3(Axi4):
    def _config(self):
        AxiLite._config(self)
        self.ID_WIDTH = Param(6)
        self.LOCK_WIDTH = Param(2)

    def _declr(self):
        with self._paramsShared():
            self.aw = Axi3_addr()
            self.ar = Axi3_addr()
            self.w = Axi3_w()
            self.r = Axi4_r(masterDir=DIRECTION.IN)
            self.b = Axi4_b(masterDir=DIRECTION.IN)

    def _getIpCoreIntfClass(self):
        return IP_Axi3


class Axi3_withAddrUser(Axi4):
    def _config(self):
        Axi4._config(self)
        self.USER_WIDTH = Param(3)

    def _declr(self):
        with self._paramsShared():
            self.aw = Axi3_addr_withUser()
            self.ar = Axi3_addr_withUser()
            self.w = Axi3_w()
            self.r = Axi4_r(masterDir=DIRECTION.IN)
            self.b = Axi4_b(masterDir=DIRECTION.IN)

    def _getIpCoreIntfClass(self):
        return IP_Axi3_withAddrUser


class IP_Axi3(IP_Axi4):
    def __init__(self):
        super(IP_Axi3, self).__init__()
        self.quartus_name = "axi"

    def postProcess(self, component, entity, allInterfaces, thisIf):
        super().postProcess(component, entity, allInterfaces, thisIf)
        prot = single(self.parameters, lambda x: x.name == "PROTOCOL")
        prot.value.text = "AXI3"


class IP_Axi3_withAddrUser(IP_Axi3):
    def __init__(self):
        super().__init__()
        AxiMap('ar', ['user'], self.map['ar'])
        AxiMap('aw', ['user'], self.map['aw'])

    def postProcess(self, component, entity, allInterfaces, thisIf):
        super().postProcess(component, entity, allInterfaces, thisIf)
        self.addWidthParam(thisIf, "AWUSER_WIDTH", thisIf.USER_WIDTH)
        self.addWidthParam(thisIf, "ARUSER_WIDTH", thisIf.USER_WIDTH)
