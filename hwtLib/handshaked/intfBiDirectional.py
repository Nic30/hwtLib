from collections import deque

from hwt.hdl.constants import DIRECTION
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, VectSignal, Signal
from pycocotb.hdlSimulator import HdlSimulator


class HandshakedBiDirectionalAgent(HandshakedAgent):
    """
    Simulation agent for :class:`.HandshakedBiDirectional` interface

    :attention: for monitor number of items in dinData
        has to match with number of received items
    """

    def __init__(self, sim, intf):
        HandshakedAgent.__init__(self, sim, intf)
        self.dinData = deque()

    def onMonitorReady(self):
        "write din"
        d = self.dinData.popleft()
        self.intf.din.write(d)

    def onDriverWriteAck(self):
        "read din"
        d = self.intf.din.read()
        self.dinData.append(d)

    def get_data(self):
        """extract data from interface"""
        return self.intf.dout.read()

    def set_data(self, data):
        """write data to interface"""
        self.intf.dout.write(data)


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

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HandshakedBiDirectionalAgent(sim, self)
