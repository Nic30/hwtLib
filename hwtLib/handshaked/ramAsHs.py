from hwt.code import If
from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import Handshaked, BramPort_withoutClk
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.simulator.agentBase import AgentBase
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.interfaces.addrDataHs import AddrDataHs


class RamHsRAgent(AgentBase):
    """
    Composite agent with agent for addr and data channel
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

        intf.addr._initSimAgent()
        self.addr = intf.addr._ag

        intf.data._initSimAgent()
        self.data = intf.data._ag

    def getDrivers(self):
        return (self.addr.getDrivers() + 
                self.data.getMonitors()
                )

    def getMonitors(self):
        return (self.addr.getMonitors() + 
                self.data.getDrivers()
                )


class RamHsR(Interface):
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        self.addr = Handshaked()
        self.addr._replaceParam("DATA_WIDTH", self.ADDR_WIDTH)
        with self._paramsShared():
            self.data = Handshaked(masterDir=DIRECTION.IN)

    def _initSimAgent(self):
        self._ag = RamHsRAgent(self)


@serializeParamsUniq
class RamAsHs(Unit):
    """
    Converter from ram port to handshaked interfaces
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.r = RamHsR()
            self.w = AddrDataHs()
            self.ram = BramPort_withoutClk()

    def _impl(self):
        r = self.r
        w = self.w
        ram = self.ram

        readRegEmpty = self._reg("readRegEmpty", defVal=1)
        readDataPending = self._reg("readDataPending", defVal=0)
        readData = self._reg("readData", r.data.data._dtype)

        rEn = readRegEmpty | r.data.rd
        readDataPending(r.addr.vld & rEn)
        If(readDataPending,
           readData(ram.dout)
        )

        If(r.data.rd,
            readRegEmpty(~readDataPending)
        ).Else(
            readRegEmpty(~(readDataPending | ~readRegEmpty))

        )

        r.addr.rd(rEn)

        If(rEn & r.addr.vld,
           ram.we(0),
           ram.addr(r.addr.data) 
        ).Else(
           ram.we(1),
           ram.addr(w.addr)
        )
        wEn = ~rEn | ~r.addr.vld
        w.rd(wEn)

        ram.din(w.data)
        ram.en((rEn & r.addr.vld) | w.vld)
        r.data.data(readData)
        r.data.vld(~readRegEmpty)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = RamAsHs()
    print(toRtl(u))
