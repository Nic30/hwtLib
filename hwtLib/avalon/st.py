from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, VectSignal, Signal
from hwt.synthesizer.param import Param


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

    def _initSimAgent(self):
        self._ag = AvalonSTAgent(self)


class AvalonSTAgent(HandshakedAgent):
    """
    Simulation Agent for AvalonST interface
    Data is stored in .data property and data format
    is tuple (channel, data, error, startOfPacket, endOfPacket)
    """

    def doRead(self, s):
        r = s.read
        intf = self.intf
        return (r(intf.channel), r(intf.data), r(intf.error),
                r(intf.startOfPacket), r(intf.endOfPacket))

    def doWrite(self, s, data):
        w = s.write
        intf = self.intf
        if data is None:
            w(None, intf.channel)
            w(None, intf.data)
            w(None, intf.error)
            w(None, intf.endOfPacket)
            w(None, intf.startOfPacket)
        else:
            channel, data, error, startOfPacket, endOfPacket  = data
            w(channel, intf.channel)
            w(data, intf.data)
            w(error, intf.error)
            w(endOfPacket, intf.endOfPacket)
            w(startOfPacket, intf.startOfPacket)

