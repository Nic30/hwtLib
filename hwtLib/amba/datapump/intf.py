from math import ceil

from hwt.hdl.constants import DIRECTION
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, VectSignal, HandshakeSync
from hwt.math import log2ceil
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream
from hwtSimApi.agents.base import AgentBase
from hwtSimApi.hdlSimulator import HdlSimulator


class AddrSizeHs(Handshaked):
    """

    :ivar MAX_LEN: maximum value of len (number of words - 1)

    .. hwt-autodoc::
    """

    def _config(self):
        self.ID_WIDTH = Param(4)
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.MAX_LEN = Param(4096 // 8 - 1)
        self.USE_STRB = Param(True)

    def _declr(self):
        if self.ID_WIDTH:
            self.id = VectSignal(self.ID_WIDTH)

        self.addr = VectSignal(self.ADDR_WIDTH)
        assert self.MAX_LEN >= 0, self.MAX_LEN
        if self.MAX_LEN > 0:
            self.len = VectSignal(log2ceil(self.MAX_LEN + 1))

        # rem is number of bytes in last word which are valid - 1
        self.rem = VectSignal(log2ceil(self.DATA_WIDTH // 8))

        HandshakeSync._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AddrSizeHsAgent(sim, self)


class AddrSizeHsAgent(HandshakedAgent):

    def get_data(self):
        intf = self.intf

        addr = intf.addr.read()
        rem = intf.rem.read()
        if intf.ID_WIDTH:
            _id = intf.id.read()
            if intf.MAX_LEN:
                _len = intf.len.read()
                return (_id, addr, _len, rem)
            else:
                return (_id, addr, rem)
        else:
            if intf.MAX_LEN:
                _len = intf.len.read()
                return (addr, _len, rem)
            else:
                return (addr, rem)

    def set_data(self, data):
        intf = self.intf

        if intf.ID_WIDTH:
            if data is None:
                _id, addr, _len, rem = (None for _ in range(4))
            else:
                if intf.MAX_LEN == 0:
                    _id, addr, rem = data
                else:
                    _id, addr, _len, rem = data

            intf.id.write(_id)
        else:
            if data is None:
                addr, _len, rem = None, None, None
            else:
                if intf.MAX_LEN == 0:
                    addr, rem = data
                else:
                    addr, _len, rem = data

        intf.addr.write(addr)
        if intf.MAX_LEN != 0:
            intf.len.write(_len)
        intf.rem.write(rem)


class AxiRDatapumpIntf(Interface):
    """
    Interface of read datapump driver

    .. hwt-autodoc::
    """

    def _config(self):
        self.ID_WIDTH = Param(0)
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)
        self.MAX_BYTES = Param(4096)
        self.USE_STRB = Param(True)

    def _declr(self):
        with self._paramsShared():
            # user requests
            self.req = AddrSizeHs()
            self.req.MAX_LEN = max(ceil(self.MAX_BYTES / (self.DATA_WIDTH // 8)) - 1, 0)
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

    .. hwt-autodoc::
    """

    def _config(self):
        AddrSizeHs._config(self)

    def _declr(self):
        with self._paramsShared():
            # user requests
            self.req = AddrSizeHs()

        with self._paramsShared(exclude=({"ID_WIDTH"}, set())):
            self.w = AxiStream()

        if self.ID_WIDTH:
            ack = Handshaked(masterDir=DIRECTION.IN)
            ack.DATA_WIDTH = self.ID_WIDTH
        else:
            ack = HandshakeSync(masterDir=DIRECTION.IN)

        self.ack = ack

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
