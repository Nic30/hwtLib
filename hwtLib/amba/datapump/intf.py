from hwt.code import log2ceil
from hwt.hdl.constants import DIRECTION
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, VectSignal, HandshakeSync
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream
from pycocotb.agents.base import AgentBase
from pycocotb.hdlSimulator import HdlSimulator


class AddrSizeHs(Handshaked):
    def _config(self):
        self.ID_WIDTH = Param(4)
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.MAX_LEN = Param(4096 // 8 - 1)
        self.USE_STRB = Param(True)

    def _declr(self):
        self.id = VectSignal(self.ID_WIDTH)

        self.addr = VectSignal(self.ADDR_WIDTH)
        #  len is number of words -1
        self.len = VectSignal(log2ceil(self.MAX_LEN))

        # rem is number of bits in last word which is valid - 1
        self.rem = VectSignal(log2ceil(self.DATA_WIDTH // 8))

        HandshakeSync._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AddrSizeHsAgent(sim, self)


class AddrSizeHsAgent(HandshakedAgent):
    def get_data(self):
        intf = self.intf

        _id = intf.id.read()
        addr = intf.addr.read()
        _len = intf.len.read()
        rem = intf.rem.read()

        return (_id, addr, _len, rem)

    def set_data(self, data):
        intf = self.intf

        if data is None:
            data = [None for _ in range(4)]

        _id, addr, _len, rem = data

        intf.id.write(_id)
        intf.addr.write(addr)
        intf.len.write(_len)
        intf.rem.write(rem)


class AxiRDatapumpIntf(Interface):
    """
    Interface of read datapump driver
    """

    def _config(self):
        AddrSizeHs._config(self)

    def _declr(self):
        with self._paramsShared():
            # user requests
            self.req = AddrSizeHs()
            self.r = AxiStream(masterDir=DIRECTION.IN)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AxiRDatapumpIntfAgent(sim, self)


class AxiRDatapumpIntfAgent(AgentBase):
    """
    Composite agent with agent for every AxiRDatapumpIntf channel
    enable is shared
    """

    @property
    def enable(self):
        return self.__enable

    @enable.setter
    def enable(self, v):
        """
        Distribute change of enable on child agents
        """
        self.__enable = v

        for o in [self.req, self.r]:
            o.enable = v

    def __init__(self, sim: HdlSimulator, intf):
        self.__enable = True
        self.intf = intf

        intf.req._initSimAgent(sim)
        self.req = intf.req._ag

        intf.r._initSimAgent(sim)
        self.r = intf.r._ag

    def getDrivers(self):
        return (self.req.getDrivers() +
                self.r.getMonitors()
                )

    def getMonitors(self):
        return (self.req.getMonitors() +
                self.r.getDrivers()
                )


class AxiWDatapumpIntf(Interface):
    """
    Interface of write datapump driver
    """

    def _config(self):
        AddrSizeHs._config(self)

    def _declr(self):
        with self._paramsShared():
            # user requests
            self.req = AddrSizeHs()

        with self._paramsShared(exclude=({"ID_WIDTH"}, set())):
            self.w = AxiStream()

        ack = self.ack = Handshaked(masterDir=DIRECTION.IN)
        ack.DATA_WIDTH = self.ID_WIDTH

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AxiWDatapumpIntfAgent(sim, self)


class AxiWDatapumpIntfAgent(AgentBase):
    """
    Composite agent with agent for every AxiRDatapumpIntf channel
    enable is shared
    """

    @property
    def enable(self):
        return self.__enable

    @enable.setter
    def enable(self, v):
        """
        Distribute change of enable on child agents
        """
        self.__enable = v

        for o in [self.req, self.w, self.ack]:
            o.enable = v

    def __init__(self, sim: HdlSimulator, intf):
        self.__enable = True
        self.intf = intf

        intf.req._initSimAgent(sim)
        self.req = intf.req._ag

        intf.w._initSimAgent(sim)
        self.w = intf.w._ag

        intf.ack._initSimAgent(sim)
        self.ack = intf.ack._ag

    def getDrivers(self):
        return (self.req.getDrivers() +
                self.w.getDrivers() +
                self.ack.getMonitors()
                )

    def getMonitors(self):
        return (self.req.getMonitors() +
                self.w.getMonitors() +
                self.ack.getDrivers()
                )
