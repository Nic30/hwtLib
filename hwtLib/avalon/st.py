from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, VectSignal, Signal
from hwt.synthesizer.param import Param
from pycocotb.hdlSimulator import HdlSimulator


class AvalonST(Handshaked):
    """
    Avalon stream interface

    :note: handshaked stream with cahnnel, error, sof, eof signal
    """

    def _config(self):
        Handshaked._config(self)
        self.CHANNEL_WIDTH = Param(1)
        self.ERROR_WIDTH = Param(1)

    def _declr(self):
        # fundamentals
        self.channel = VectSignal(self.CHANNEL_WIDTH)
        self.error = VectSignal(self.ERROR_WIDTH)
        Handshaked._declr(self)

        # packet transfer signals
        self.endOfPacket = Signal()
        self.startOfPacket = Signal()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AvalonSTAgent(sim, self)


class AvalonSTAgent(HandshakedAgent):
    """
    Simulation Agent for AvalonST interface
    Data is stored in .data property and data format
    is tuple (channel, data, error, startOfPacket, endOfPacket)
    """

    def get_data(self):
        intf = self.intf
        return (intf.channel.read(), intf.data.read(), intf.error.read(),
                intf.startOfPacket.read(), intf.endOfPacket.read())

    def set_data(self, data):
        intf = self.intf
        if data is None:
            intf.channel.write(None)
            intf.data.write(None)
            intf.error.write(None)
            intf.endOfPacket.write(None)
            intf.startOfPacket.write(None)
        else:
            channel, data, error, startOfPacket, endOfPacket = data
            intf.channel.write(channel)
            intf.data.write(data)
            intf.error.write(error)
            intf.endOfPacket.write(endOfPacket)
            intf.startOfPacket.write(startOfPacket)
