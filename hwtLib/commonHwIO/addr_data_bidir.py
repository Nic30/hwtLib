from hwt.hwIOs.std import HwIOVectSignal, HwIORdVldSync
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.handshaked.hwIOBiDirectional import HwIORdVldSyncBiDirectionalData, \
    HwIORdVldSyncBiDirectionalDataAgent
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION


class HwIOAddrOutDataInRdVld(HwIORdVldSyncBiDirectionalData):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.ADDR_WIDTH = HwParam(32)
        self.DATA_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        self.addr = HwIOVectSignal(self.ADDR_WIDTH)
        self.data = HwIOVectSignal(self.DATA_WIDTH, masterDir=DIRECTION.IN)
        HwIORdVldSync.hwDeclr(self)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOAddrOutDataInRdVldAgent(sim, self)


class HwIOAddrOutDataInRdVldAgent(HwIORdVldSyncBiDirectionalDataAgent):
    """
    Simulation agent for :class:`.HwIOAddrOutDataInRdVld` interface
    """

    @override
    def onMonitorReady(self):
        d = self.dinData.popleft()
        self.hwIO.data.write(d)

    @override
    def onDriverWriteAck(self):
        d = self.hwIO.data.read()
        self.dinData.append(d)

    @override
    def get_data(self):
        return self.hwIO.addr.read()

    @override
    def set_data(self, data):
        self.hwIO.addr.write(data)


class HwIOAddrInOutDataInRdVld(HwIORdVldSyncBiDirectionalData):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.ADDR_WIDTH = HwParam(32)
        self.DATA_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        self.addrIn = HwIOVectSignal(self.ADDR_WIDTH, masterDir=DIRECTION.IN)
        self.addrOut = HwIOVectSignal(self.ADDR_WIDTH)
        self.data = HwIOVectSignal(self.DATA_WIDTH, masterDir=DIRECTION.IN)
        HwIORdVldSync.hwDeclr(self)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOAddrInOutDataInRdVldAgent(sim, self)


class HwIOAddrInOutDataInRdVldAgent(HwIORdVldSyncBiDirectionalDataAgent):
    """
    Simulation agent for :class:`.HwIOAddrInOutDataInRdVld` interface
    """

    @override
    def onMonitorReady(self):
        a, d = self.dinData.popleft()
        self.hwIO.addrIn.write(a)
        self.hwIO.data.write(d)

    @override
    def onDriverWriteAck(self):
        a = self.hwIO.data.read()
        d = self.hwIO.data.read()
        self.dinData.append((a, d))

    @override
    def get_data(self):
        return self.hwIO.addrOut.read()

    @override
    def set_data(self, data):
        self.hwIO.addrOut.write(data)


class HwIOAddrInDataOutRdVld(HwIORdVldSyncBiDirectionalData):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.ADDR_WIDTH = HwParam(32)
        self.DATA_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        self.addr = HwIOVectSignal(self.ADDR_WIDTH, masterDir=DIRECTION.IN)
        self.data = HwIOVectSignal(self.DATA_WIDTH)
        HwIORdVldSync.hwDeclr(self)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOAddrInDataOutRdVldAgent(sim, self)


class HwIOAddrInDataOutRdVldAgent(HwIORdVldSyncBiDirectionalDataAgent):
    """
    Simulation agent for :class:`.AddrDataOutInHs` interface
    """

    @override
    def onMonitorReady(self):
        d = self.dinData.popleft()
        self.hwIO.addr.write(d)

    @override
    def onDriverWriteAck(self):
        d = self.hwIO.addr.read()
        self.dinData.append(d)

    @override
    def get_data(self):
        return self.hwIO.data.read()

    @override
    def set_data(self, data):
        self.hwIO.data.write(data)

