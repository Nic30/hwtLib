from hwt.code import log2ceil
from hwt.hdl.constants import DIRECTION
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, VectSignal, HandshakeSync
from hwt.simulator.agentBase import AgentBase
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream_withId, AxiStream


class AddrSizeHs(Handshaked):
    def _config(self):
        self.ID_WIDTH = Param(4)
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.MAX_LEN = Param(4096 // 8 - 1)

    def _declr(self):
        self.id = VectSignal(self.ID_WIDTH)

        self.addr = VectSignal(self.ADDR_WIDTH)
        #  len is number of words -1
        self.len = VectSignal(log2ceil(self.MAX_LEN))

        # rem is number of bits in last word which is valid - 1
        self.rem = VectSignal(log2ceil(self.DATA_WIDTH // 8))

        HandshakeSync._declr(self)

    def _initSimAgent(self):
        self._ag = AddrSizeHsAgent(self)


class AddrSizeHsAgent(HandshakedAgent):
    def doRead(self, s):
        intf = self.intf
        r = s.read

        _id = r(intf.id)
        addr = r(intf.addr)
        _len = r(intf.len)
        rem = r(intf.rem)

        return (_id, addr, _len, rem)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.write

        if data is None:
            data = [None for _ in range(4)]

        _id, addr, _len, rem = data

        w(_id, intf.id)
        w(addr, intf.addr)
        w(_len, intf.len)
        w(rem, intf.rem)


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
            self.r = AxiStream_withId(masterDir=DIRECTION.IN)

    def _initSimAgent(self):
        self._ag = AxiRDatapumpIntfAgent(self)


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

    def __init__(self, intf):
        self.__enable = True
        self.intf = intf

        intf.req._initSimAgent()
        self.req = intf.req._ag

        intf.r._initSimAgent()
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
            self.w = AxiStream()

        self.ack = Handshaked(masterDir=DIRECTION.IN)
        self.ack._replaceParam("DATA_WIDTH", self.ID_WIDTH)

    def _initSimAgent(self):
        self._ag = AxiWDatapumpIntfAgent(self)


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

    def __init__(self, intf):
        self.__enable = True
        self.intf = intf

        intf.req._initSimAgent()
        self.req = intf.req._ag

        intf.w._initSimAgent()
        self.w = intf.w._ag

        intf.ack._initSimAgent()
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
