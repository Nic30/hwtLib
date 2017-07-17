from collections import deque

from hwt.hdlObjects.constants import DIRECTION
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, VectSignal, Signal


class HandshakedBiDirectionalAgent(HandshakedAgent):
    """
    Simulation agent for :class:`.HandshakedBiDirectional` interface

    :attention: for monitor number of items in dinData has to match with number of received items
    """
    def __init__(self, intf):
        HandshakedAgent.__init__(self, intf)
        self.dinData = deque()

    def onMonitorReady(self, simulator):
        "write din"
        d = self.dinData.popleft()
        simulator.write(d, self.intf.din)

    def onDriverWirteAck(self, simulator):
        "read din"
        d = simulator.read(self.intf.din)
        self.dinData.append(d)

    def doRead(self, s):
        """extract data from interface"""
        return s.read(self.intf.dout)

    def doWrite(self, s, data):
        """write data to interface"""
        s.write(data, self.intf.dout)


class HandshakedBiDirectional(Handshaked):
    """
    :class:`hwt.interfaces.std.Handshaked` interface with data
        channels in bout direction
    """
    def _declr(self):
        self.din = VectSignal(self.DATA_WIDTH, masterDir=DIRECTION.IN)
        self.dout = VectSignal(self.DATA_WIDTH)
        self.vld = Signal()
        self.rd = Signal(masterDir=DIRECTION.IN)

    def _getSimAgent(self):
        return HandshakedBiDirectionalAgent
