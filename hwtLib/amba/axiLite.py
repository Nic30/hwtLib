from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import VectSignal
from hwt.serializer.ip_packager.interfaces.intfConfig import IntfConfig
from hwt.simulator.agentBase import AgentBase
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.amba.axi_intf_common import AxiMap, Axi_hs
from hwtLib.amba.sim.agentCommon import BaseAxiAgent


#################################################################
class AxiLite_addr(Axi_hs):
    def _config(self):
        self.ADDR_WIDTH = Param(32)

    def _declr(self):
        self.addr = VectSignal(self.ADDR_WIDTH)
        Axi_hs._declr(self)

    def _initSimAgent(self):
        self._ag = AxiLite_addrAgent(self)


class AxiLite_addrAgent(BaseAxiAgent):
    """
    :ivar data: iterable of addr
    """
    def doRead(self, s):
        return s.read(self.intf.addr)

    def doWrite(self, s, data):
        s.write(data, self.intf.addr)


#################################################################
class AxiLite_r(Axi_hs):
    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.data = VectSignal(self.DATA_WIDTH)
        self.resp = VectSignal(2)
        Axi_hs._declr(self)

    def _initSimAgent(self):
        self._ag = AxiLite_rAgent(self)


class AxiLite_rAgent(BaseAxiAgent):
    """
    :ivar data: iterable of tuples (data, resp)
    """
    def doRead(self, s):
        r = s.read
        intf = self.intf

        return (r(intf.data), r(intf.resp))

    def doWrite(self, s, data):
        intf = self.intf
        w = s.write
        if data is None:
            data = [None for _ in range(2)]

        data, resp = data

        w(data, intf.data)
        w(resp, intf.resp)


#################################################################
class AxiLite_w(Axi_hs):
    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.data = VectSignal(self.DATA_WIDTH)
        self.strb = VectSignal(self.DATA_WIDTH // 8)
        Axi_hs._declr(self)

    def _initSimAgent(self):
        self._ag = AxiLite_wAgent(self)


class AxiLite_wAgent(BaseAxiAgent):
    """
    :ivar data: iterable of tuples (data, strb)
    """
    def doRead(self, s):
        intf = self.intf
        r = s.read
        return (r(intf.data), r(intf.strb))

    def doWrite(self, s, data):
        intf = self.intf
        w = s.write
        if data is None:
            w(None, intf.data)
            w(None, intf.strb)
        else:
            data, strb = data
            w(data, intf.data)
            w(strb, intf.strb)


#################################################################
class AxiLite_b(Axi_hs):
    def _declr(self):
        self.resp = VectSignal(2)
        Axi_hs._declr(self)

    def _initSimAgent(self):
        self._ag = AxiLite_bAgent(self)


class AxiLite_bAgent(BaseAxiAgent):
    """
    :ivar data: iterable of resp
    """
    def doRead(self, s):
        return s.read(self.intf.resp)

    def doWrite(self, s, data):
        s.write(data, self.intf.resp)


#################################################################
class AxiLite(Interface):
    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        with self._paramsShared():
            self.aw = AxiLite_addr()
            self.ar = AxiLite_addr()
            self.w = AxiLite_w()
            self.r = AxiLite_r(masterDir=DIRECTION.IN)
            self.b = AxiLite_b(masterDir=DIRECTION.IN)

    def _getIpCoreIntfClass(self):
        return IP_AXILite

    def _initSimAgent(self):
        self._ag = AxiLiteAgent(self)

    def _getWordAddrStep(self):
        """
        :return: size of one word in unit of address
        """
        return int(self.DATA_WIDTH) // self._getAddrStep()

    def _getAddrStep(self):
        """
        :return: how many bits is one unit of address (f.e. 8 bits for  char * pointer,
             36 for 36 bit bram)
        """
        return 8


class AxiLiteAgent(AgentBase):
    """
    Composite simulation agent with agent for every axi channel
    change of enable is propagated to each child

    data for each agent is stored in agent for given channel (ar, aw, r, ... property)
    """

    def __init__(self, intf):
        self.__enable = True
        self.intf = intf

        def ag(intf):
            intf._initSimAgent()
            agent = intf._ag
            return agent

        self.ar = ag(intf.ar)
        self.aw = ag(intf.aw)
        self.r = ag(intf.r)
        self.w = ag(intf.w)
        self.b = ag(intf.b)

    def getEnable(self):
        return self.__enable

    def setEnable(self, en, sim):
        if self.__enable != en:
            self.__enable = en
    
            for o in [self.ar, self.aw, self.r, self.w, self.b]:
                o.setEnable(en, sim)

    def getDrivers(self):
        return (self.aw.getDrivers() +
                self.ar.getDrivers() +
                self.w.getDrivers() +
                self.r.getMonitors() +
                self.b.getMonitors()
                )

    def getMonitors(self):
        return (self.aw.getMonitors() +
                self.ar.getMonitors() +
                self.w.getMonitors() +
                self.r.getDrivers() +
                self.b.getDrivers()
                )


#################################################################
class IP_AXILite(IntfConfig):
    def __init__(self):
        super().__init__()
        self.name = "aximm"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        a_sigs = ['addr', 'valid', 'ready']
        self.map = {'aw': AxiMap('aw', a_sigs),
                    'w': AxiMap('w', ['data', 'strb', 'valid', 'ready']),
                    'ar': AxiMap('ar', a_sigs),
                    'r': AxiMap('r', ['data', 'resp', 'valid', 'ready']),
                    'b': AxiMap('b', ['valid', 'ready', 'resp'])
                    }

    def postProcess(self, component, entity, allInterfaces, thisIf):
        self.endianness = "little"
        self.addWidthParam(thisIf, "ADDR_WIDTH", thisIf.ADDR_WIDTH)
        self.addWidthParam(thisIf, "DATA_WIDTH", thisIf.DATA_WIDTH)
        self.addSimpleParam(thisIf, "PROTOCOL", "AXI4LITE")
        self.addSimpleParam(thisIf, "READ_WRITE_MODE", "READ_WRITE")
