from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIODataRdVld, HwIOVectSignal, HwIOSignal
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtSimApi.hdlSimulator import HdlSimulator


class AvalonST(HwIODataRdVld):
    """
    Avalon stream interface

    :note: handshaked stream with channel, error, sof, eof signal

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        HwIODataRdVld.hwConfig(self)
        self.CHANNEL_WIDTH = HwParam(1)
        self.ERROR_WIDTH = HwParam(1)

    @override
    def hwDeclr(self):
        # fundamentals
        self.channel = HwIOVectSignal(self.CHANNEL_WIDTH)
        self.error = HwIOVectSignal(self.ERROR_WIDTH)
        HwIODataRdVld.hwDeclr(self)

        # packet transfer signals
        self.endOfPacket = HwIOSignal()
        self.startOfPacket = HwIOSignal()

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AvalonSTAgent(sim, self)


class AvalonSTAgent(HwIODataRdVldAgent):
    """
    Simulation Agent for AvalonST interface
    Data is stored in .data property and data format
    is tuple (channel, data, error, startOfPacket, endOfPacket)
    """

    @override
    def get_data(self):
        hwIO = self.hwIO
        return (hwIO.channel.read(), hwIO.data.read(), hwIO.error.read(),
                hwIO.startOfPacket.read(), hwIO.endOfPacket.read())

    @override
    def set_data(self, data):
        hwIO = self.hwIO
        if data is None:
            hwIO.channel.write(None)
            hwIO.data.write(None)
            hwIO.error.write(None)
            hwIO.endOfPacket.write(None)
            hwIO.startOfPacket.write(None)
        else:
            channel, data, error, startOfPacket, endOfPacket = data
            hwIO.channel.write(channel)
            hwIO.data.write(data)
            hwIO.error.write(error)
            hwIO.endOfPacket.write(endOfPacket)
            hwIO.startOfPacket.write(startOfPacket)
