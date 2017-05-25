from hwt.hdlObjects.constants import DIRECTION
from hwt.interfaces.std import VectSignal
from hwt.pyUtils.arrayQuery import single
from hwt.synthesizer.param import Param
from hwtLib.amba.axi4 import IP_Axi4, Axi4_w, Axi4_r, Axi4_b, Axi4, \
    Axi4_addr
from hwtLib.amba.axi_intf_common import AxiMap
from hwtLib.amba.sim.agentCommon import BaseAxiAgent


class Axi3_addr(Axi4_addr):
    def _config(self):
        Axi4_addr._config(self)
        self.LEN_WIDTH = 4

    def _getIpCoreIntfClass(self):
        return IP_Axi3


class Axi3_addr_withUser(Axi3_addr):
    def _config(self):
        Axi3_addr._config(self)
        self.USER_WIDTH = Param(5)

    def _declr(self):
        Axi3_addr._declr(self)
        self.user = VectSignal(self.USER_WIDTH)

    def _getSimAgent(self):
        return Axi3_addr_withUserAgent


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
        qos = r(intf.qos)
        user = r(intf.user)
        return (_id, addr, burst, cache, _len, lock, prot, size, qos, user)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.write

        if data is None:
            data = [None for _ in range(10)]

        _id, addr, burst, cache, _len, lock, prot, size, qos, user = data

        w(_id, intf.id)
        w(addr, intf.addr)
        w(burst, intf.burst)
        w(cache, intf.cache)
        w(_len, intf.len)
        w(lock, intf.lock)
        w(prot, intf.prot)
        w(size, intf.size)
        w(qos, intf.qos)
        w(user, intf.user)


class Axi3(Axi4):
    def _declr(self):
        with self._paramsShared():
            self.aw = Axi3_addr()
            self.ar = Axi3_addr()
            self.w = Axi4_w()
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
            self.w = Axi4_w()
            self.r = Axi4_r(masterDir=DIRECTION.IN)
            self.b = Axi4_b(masterDir=DIRECTION.IN)

    def _getIpCoreIntfClass(self):
        return IP_Axi3_withAddrUser


class IP_Axi3(IP_Axi4):
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
