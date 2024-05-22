from collections import deque

from hwt.constants import DIRECTION
from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIODataRdVld, HwIOVectSignal, HwIOSignal
from hwtSimApi.hdlSimulator import HdlSimulator
from hwt.pyUtils.typingFuture import override


class HwIORdVldSyncBiDirectionalData(HwIODataRdVld):
    """
    :class:`hwt.hwIOs.std.HwIODataRdVld` interface with data
        channels in bout direction

    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.din = HwIOVectSignal(self.DATA_WIDTH, masterDir=DIRECTION.IN)
        self.dout = HwIOVectSignal(self.DATA_WIDTH)
        self.vld = HwIOSignal()
        self.rd = HwIOSignal(masterDir=DIRECTION.IN)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIORdVldSyncBiDirectionalDataAgent(sim, self)


class HwIORdVldSyncBiDirectionalDataAgent(HwIODataRdVldAgent):
    """
    Simulation agent for :class:`.HwIORdVldSyncBiDirectionalData` interface

    :attention: for monitor number of items in dinData
        has to match with number of received items
    """

    def __init__(self, sim, hwIO):
        HwIODataRdVldAgent.__init__(self, sim, hwIO)
        self.dinData = deque()
        self._isMonitor = False

    @override
    def getMonitors(self):
        self._isMonitor = True
        return HwIODataRdVldAgent.getMonitors(self)

    @override
    def notReset(self):
        nr = HwIODataRdVldAgent.notReset(self)
        if self._isMonitor:
            return nr and self.dinData
        else:
            return nr

    @override
    def onMonitorReady(self):
        "write din"
        d = self.dinData.popleft()
        self.hwIO.din.write(d)

    @override
    def onDriverWriteAck(self):
        "read din"
        d = self.hwIO.din.read()
        self.dinData.append(d)

    @override
    def get_data(self):
        """extract data from interface"""
        return self.hwIO.dout.read()

    @override
    def set_data(self, data):
        """write data to interface"""
        self.hwIO.dout.write(data)

