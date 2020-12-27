from hwt.interfaces.std import VectSignal, HandshakeSync
from hwt.synthesizer.param import Param
from hwtLib.handshaked.intfBiDirectional import HandshakedBiDirectional, \
    HandshakedBiDirectionalAgent
from ipCorePackager.constants import DIRECTION
from hwtSimApi.hdlSimulator import HdlSimulator


class AddrOutDataInHs(HandshakedBiDirectional):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        self.addr = VectSignal(self.ADDR_WIDTH)
        self.data = VectSignal(self.DATA_WIDTH, masterDir=DIRECTION.IN)
        HandshakeSync._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AddrOutDataInHsAgent(sim, self)


class AddrOutDataInHsAgent(HandshakedBiDirectionalAgent):
    """
    Simulation agent for :class:`.AddrOutDataInHs` interface
    """

    def onMonitorReady(self):
        d = self.dinData.popleft()
        self.intf.data.write(d)

    def onDriverWriteAck(self):
        d = self.intf.data.read()
        self.dinData.append(d)

    def get_data(self):
        return self.intf.addr.read()

    def set_data(self, data):
        self.intf.addr.write(data)


class AddrInOutDataInHs(HandshakedBiDirectional):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        self.addrIn = VectSignal(self.ADDR_WIDTH, masterDir=DIRECTION.IN)
        self.addrOut = VectSignal(self.ADDR_WIDTH)
        self.data = VectSignal(self.DATA_WIDTH, masterDir=DIRECTION.IN)
        HandshakeSync._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AddrInOutDataInHsAgent(sim, self)


class AddrInOutDataInHsAgent(HandshakedBiDirectionalAgent):
    """
    Simulation agent for :class:`.AddrInOutDataInHs` interface
    """

    def onMonitorReady(self):
        a, d = self.dinData.popleft()
        self.intf.addrIn.write(a)
        self.intf.data.write(d)

    def onDriverWriteAck(self):
        a = self.intf.data.read()
        d = self.intf.data.read()
        self.dinData.append((a, d))

    def get_data(self):
        return self.intf.addrOut.read()

    def set_data(self, data):
        self.intf.addrOut.write(data)


class AddrInDataOutHs(HandshakedBiDirectional):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        self.addr = VectSignal(self.ADDR_WIDTH, masterDir=DIRECTION.IN)
        self.data = VectSignal(self.DATA_WIDTH)
        HandshakeSync._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AddrInDataOutHsAgent(sim, self)


class AddrInDataOutHsAgent(HandshakedBiDirectionalAgent):
    """
    Simulation agent for :class:`.AddrDataOutInHs` interface
    """

    def onMonitorReady(self):
        d = self.dinData.popleft()
        self.intf.addr.write(d)

    def onDriverWriteAck(self):
        d = self.intf.addr.read()
        self.dinData.append(d)

    def get_data(self):
        return self.intf.data.read()

    def set_data(self, data):
        self.intf.data.write(data)

