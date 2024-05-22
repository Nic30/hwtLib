from math import ceil

from hwt.constants import DIRECTION
from hwt.hwParam import HwParam
from hwt.hwIO import HwIO
from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIODataRdVld, HwIOVectSignal, HwIORdVldSync
from hwt.math import log2ceil
from hwtLib.amba.axi4s import Axi4Stream
from hwtSimApi.agents.base import AgentBase
from hwtSimApi.hdlSimulator import HdlSimulator


class AddrSizeHs(HwIODataRdVld):
    """

    :ivar MAX_LEN: maximum value of len (number of words - 1)

    .. hwt-autodoc::
    """

    def _config(self):
        self.ID_WIDTH = HwParam(4)
        self.ADDR_WIDTH = HwParam(32)
        self.DATA_WIDTH = HwParam(64)
        self.MAX_LEN = HwParam(4096 // 8 - 1)
        self.USE_STRB = HwParam(True)

    def _declr(self):
        if self.ID_WIDTH:
            self.id = HwIOVectSignal(self.ID_WIDTH)

        self.addr = HwIOVectSignal(self.ADDR_WIDTH)
        assert self.MAX_LEN >= 0, self.MAX_LEN
        if self.MAX_LEN > 0:
            self.len = HwIOVectSignal(log2ceil(self.MAX_LEN + 1))

        # rem is number of bytes in last word which are valid - 1
        self.rem = HwIOVectSignal(log2ceil(self.DATA_WIDTH // 8))

        HwIORdVldSync._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AddrSizeHsAgent(sim, self)


class AddrSizeHsAgent(HwIODataRdVldAgent):

    def get_data(self):
        hwIO = self.hwIO

        addr = hwIO.addr.read()
        rem = hwIO.rem.read()
        if hwIO.ID_WIDTH:
            _id = hwIO.id.read()
            if hwIO.MAX_LEN:
                _len = hwIO.len.read()
                return (_id, addr, _len, rem)
            else:
                return (_id, addr, rem)
        else:
            if hwIO.MAX_LEN:
                _len = hwIO.len.read()
                return (addr, _len, rem)
            else:
                return (addr, rem)

    def set_data(self, data):
        hwIO = self.hwIO

        if hwIO.ID_WIDTH:
            if data is None:
                _id, addr, _len, rem = (None for _ in range(4))
            else:
                if hwIO.MAX_LEN == 0:
                    _id, addr, rem = data
                else:
                    _id, addr, _len, rem = data

            hwIO.id.write(_id)
        else:
            if data is None:
                addr, _len, rem = None, None, None
            else:
                if hwIO.MAX_LEN == 0:
                    addr, rem = data
                else:
                    addr, _len, rem = data

        hwIO.addr.write(addr)
        if hwIO.MAX_LEN != 0:
            hwIO.len.write(_len)
        hwIO.rem.write(rem)


class HwIOAxiRDatapump(HwIO):
    """
    HwIO of read datapump driver

    .. hwt-autodoc::
    """

    def _config(self):
        self.ID_WIDTH = HwParam(0)
        self.ADDR_WIDTH = HwParam(32)
        self.DATA_WIDTH = HwParam(64)
        self.MAX_BYTES = HwParam(4096)
        self.USE_STRB = HwParam(True)

    def _declr(self):
        with self._hwParamsShared():
            # user requests
            self.req = AddrSizeHs()
            self.req.MAX_LEN = max(ceil(self.MAX_BYTES / (self.DATA_WIDTH // 8)) - 1, 0)
            self.r = Axi4Stream(masterDir=DIRECTION.IN)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOAxiRDatapumpAgent(sim, self)


class HwIOAxiRDatapumpAgent(AgentBase):
    """
    Composite agent with agent for every HwIOAxiRDatapump channel
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

    def __init__(self, sim: HdlSimulator, hwIO):
        self.__enable = True
        self.hwIO = hwIO

        hwIO.req._initSimAgent(sim)
        self.req = hwIO.req._ag

        hwIO.r._initSimAgent(sim)
        self.r = hwIO.r._ag

    def getDrivers(self):
        yield from self.req.getDrivers()
        yield from self.r.getMonitors()

    def getMonitors(self):
        yield from self.req.getMonitors()
        yield from self.r.getDrivers()


class HwIOAxiWDatapump(HwIO):
    """
    HwIO of write datapump driver

    .. hwt-autodoc::
    """

    def _config(self):
        AddrSizeHs._config(self)

    def _declr(self):
        with self._hwParamsShared():
            # user requests
            self.req = AddrSizeHs()

        with self._hwParamsShared(exclude=({"ID_WIDTH"}, set())):
            self.w = Axi4Stream()

        if self.ID_WIDTH:
            ack = HwIODataRdVld(masterDir=DIRECTION.IN)
            ack.DATA_WIDTH = self.ID_WIDTH
        else:
            ack = HwIORdVldSync(masterDir=DIRECTION.IN)

        self.ack = ack

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOAxiWDatapumpAgent(sim, self)


class HwIOAxiWDatapumpAgent(AgentBase):
    """
    Composite agent with agent for every HwIOAxiRDatapump channel
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

    def __init__(self, sim: HdlSimulator, hwIO):
        self.__enable = True
        self.hwIO = hwIO

        hwIO.req._initSimAgent(sim)
        self.req = hwIO.req._ag

        hwIO.w._initSimAgent(sim)
        self.w = hwIO.w._ag

        hwIO.ack._initSimAgent(sim)
        self.ack = hwIO.ack._ag

    def getDrivers(self):
        yield from self.req.getDrivers()
        yield from self.w.getDrivers()
        yield from self.ack.getMonitors()

    def getMonitors(self):
        yield from self.req.getMonitors()
        yield from self.w.getMonitors()
        yield from self.ack.getDrivers()
